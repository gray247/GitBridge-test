#!/usr/bin/env python3
"""
GitBridge — Stable Flask backend with enhanced error handling and safety
• Implements Git locking to prevent race conditions (cross-platform via filelock)
• Enhanced error handling and logging
• Path validation for security
• Profile switching support
• Robust commit/push operations
• Secure clone using GIT_ASKPASS helper
"""
import os
import json
import shutil
import subprocess
import time
import logging
from pathlib import Path
from contextlib import contextmanager
from functools import wraps

from filelock import FileLock, Timeout
from flask import Flask, jsonify, request

# ---------------------------------------------------------------------
# 0. LOGGING SETUP
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gitbridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# 1. CONFIG / PROFILE
# ---------------------------------------------------------------------
PROFILE_PATH = Path("profiles/active.json")

def load_profile():
    """Load and validate profile configuration"""
    if not PROFILE_PATH.exists():
        raise FileNotFoundError(f"Missing profile: {PROFILE_PATH}")
    try:
        profile = json.loads(PROFILE_PATH.read_text())
        required_keys = ["repo", "token", "local_folder"]
        missing = [k for k in required_keys if k not in profile]
        if missing:
            raise ValueError(f"Profile missing required keys: {missing}")
        return profile
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in profile: {e}")

# Attempt graceful profile load
try:
    profile = load_profile()
except Exception as e:
    logger.critical(f"Could not load active profile: {e}")
    profile = {}

REPO = profile.get("repo", "")
TOKEN = profile.get("token", os.getenv("GITHUB_TOKEN", ""))
LOCAL_FOLDER = Path(profile.get("local_folder", "local_repo"))
# Safe mode can be overridden via env var or profile
SAFE_MODE = os.getenv("GITBRIDGE_SAFE_MODE", str(profile.get("safe_mode", True))).lower() == "true"

# ---------------------------------------------------------------------
# 2. SECURITY & VALIDATION
# ---------------------------------------------------------------------
def validate_path(path_str: str) -> Path:
    """Validate and sanitize file paths to prevent directory traversal"""
    if not path_str:
        raise ValueError("Path cannot be empty")
    for pattern in ('..', '~', '$', '`', '|', ';', '&', '\x00'):
        if pattern in path_str:
            raise ValueError(f"Path contains dangerous pattern: {pattern}")
    if path_str.startswith('/') or (len(path_str) > 1 and path_str[1] == ':'):
        raise ValueError("Absolute paths not allowed")
    full_path = (LOCAL_FOLDER / path_str).resolve()
    try:
        full_path.relative_to(LOCAL_FOLDER.resolve())
    except ValueError:
        raise ValueError("Path outside repository boundaries")
    return full_path

# ---------------------------------------------------------------------
# 3. GIT OPERATIONS WITH LOCKING
# ---------------------------------------------------------------------
LOCK_PATH = LOCAL_FOLDER / ".git_lock"

@contextmanager
def git_lock(timeout: int = 30):
    """Ensure only one Git operation at a time (cross-platform)"""
    lock = FileLock(str(LOCK_PATH))
    try:
        lock.acquire(timeout=timeout)
        logger.info("Acquired Git lock")
        yield
n    except Timeout:
        raise Exception("Could not acquire Git lock within timeout period")
    finally:
        if lock.is_locked:
            lock.release()
            logger.info("Released Git lock")


def safe_git_operation(cmd, cwd=None, timeout=30):
    """Execute Git command with proper error handling"""
    cwd = cwd or LOCAL_FOLDER
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout
        )
        logger.info(f"Git command successful: {' '.join(cmd)}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {' '.join(cmd)}, error: {e.stderr}")
        raise
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out: {' '.join(cmd)}")
        raise


def commit_push_safe(msg: str) -> bool:
    """Safe commit and push with retries"""
    retries = 3
    for i in range(retries):
        try:
            with git_lock():
                status = safe_git_operation(["git", "status", "--porcelain"]).stdout
                if not status.strip():
                    logger.info("No changes to commit")
                    return True
                safe_git_operation(["git", "add", "."])
                safe_git_operation(["git", "commit", "-m", msg])
                try:
                    safe_git_operation(["git", "pull", "origin", "main", "--rebase"] )
                except subprocess.CalledProcessError:
                    logger.warning("Pull failed, continuing with push")
                safe_git_operation(["git", "push", "origin", "HEAD:main"] )
                logger.info(f"Committed and pushed: {msg}")
                return True
        except Exception as e:
            logger.error(f"Attempt {i+1}/{retries} failed: {e}")
            if i == retries - 1:
                raise
            time.sleep(2 ** i)
    return False

# ---------------------------------------------------------------------
# 4. GIT SETUP (Secure Clone)
# ---------------------------------------------------------------------
def ensure_repository():
    """Ensure repository exists, clone if missing, and update main branch"""
    if not LOCAL_FOLDER.exists():
        logger.info("Cloning repository...")
        # generate a simple askpass helper script
        helper = LOCAL_FOLDER.parent / ".git_askpass.sh"
        helper.write_text(f"#!/bin/sh\necho {TOKEN}")
        helper.chmod(0o700)
        env = os.environ.copy()
        env.update({"GIT_ASKPASS": str(helper), "GITHUB_TOKEN": TOKEN})
        subprocess.run(
            ["git", "clone", f"https://github.com/{REPO}.git", str(LOCAL_FOLDER)],
            check=True,
            timeout=60,
            env=env
        )
        logger.info("Repository cloned successfully")
    try:
        safe_git_operation(["git", "checkout", "-B", "main"])
        safe_git_operation(["git", "pull", "origin", "main"])
        logger.info("Repository is ready on main branch")
    except Exception:
        logger.warning("Could not checkout/pull main; continuing")

# Initialize repository
ensure_repository()

# ---------------------------------------------------------------------
# 5. ERROR HANDLING DECORATOR
# ---------------------------------------------------------------------
def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git error in {f.__name__}: {e.stderr}")
            return jsonify(error=f"Git operation failed: {e.stderr}"), 500
        except (FileNotFoundError, PermissionError, ValueError) as e:
            code = 404 if isinstance(e, FileNotFoundError) else 403 if isinstance(e, PermissionError) else 400
            return jsonify(error=str(e)), code
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify(error="Internal server error"), 500
    return wrapper

# ---------------------------------------------------------------------
# 6. FLASK APP
# ---------------------------------------------------------------------
app = Flask(__name__)
logger.info("GitBridge backend starting...")
logger.info(f"Repository: {REPO}")
logger.info(f"Local folder: {LOCAL_FOLDER.resolve()}")
logger.info(f"Safe mode: {SAFE_MODE}")

# Helper: atomic write

