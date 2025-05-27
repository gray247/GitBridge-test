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
    except Timeout:
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
                    safe_git_operation(["git", "pull", "origin", "main", "--rebase"])
                except subprocess.CalledProcessError:
                    logger.warning("Pull failed, continuing with push")
                safe_git_operation(["git", "push", "origin", "HEAD:main"])
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
    try:
        if not LOCAL_FOLDER.exists():
            logger.info("Cloning repository...")
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
        safe_git_operation(["git", "checkout", "-B", "main"])
        safe_git_operation(["git", "pull", "origin", "main"])
        logger.info("Repository is ready on main branch")
    except OSError as e:
        logger.warning(f"OS error in ensure_repository (skipping clone/setup): {e}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git operation failed during ensure_repository: {e}")

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
# 6. FLASK APP & ROUTES
# ---------------------------------------------------------------------
app = Flask(__name__)
logger.info("GitBridge backend starting...")
logger.info(f"Repository: {REPO}")
logger.info(f"Local folder: {LOCAL_FOLDER.resolve()}")
logger.info(f"Safe mode: {SAFE_MODE}")


def write_file_safe(path: Path, content: str) -> None:
    """Safely write file with atomic rename"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(content, encoding='utf-8')
        tmp.rename(path)
        logger.info(f"File written successfully: {path}")
    except Exception as e:
        logger.error(f"Failed to write file {path}: {e}")
        raise

@app.get("/")
@handle_errors
def index():
    return jsonify(
        status="GitBridge is live",
        version="2.0-stable",
        endpoints=["/upload","/move","/delete","/tree","/profiles","/health","/verify_upload"],
        active_profile=profile.get("name","unknown")
    )

@app.post("/upload")
@handle_errors
def upload():
    data = request.get_json(force=True)
    if not data or "path" not in data or "content" not in data:
        return jsonify(error="Missing required: path, content"), 400
    file_path = validate_path(data["path"])
    write_file_safe(file_path, data["content"])
    commit_push_safe(f"Upload {data['path']}")
    return jsonify(status="success", path=data["path"])  

@app.post("/move")
@handle_errors
def move():
    data = request.get_json(force=True)
    if not data or "src" not in data or "dst" not in data:
        return jsonify(error="Missing required: src, dst"), 400
    src = validate_path(data["src"])
    dst = validate_path(data["dst"])
    if not src.exists():
        return jsonify(error="Source not found"), 404
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    commit_push_safe(f"Move {data['src']} to {data['dst']}")
    return jsonify(status="success", from_=data["src"], to=data["dst"])  

@app.post("/delete")
@handle_errors
def delete():
    data = request.get_json(force=True)
    if not data or "path" not in data:
        return jsonify(error="Missing required: path"), 400
    if SAFE_MODE:
        return jsonify(error="Deletion disabled (safe mode)"), 403
    fp = validate_path(data["path"])
    if not fp.exists():
        return jsonify(error="File not found"), 404
    fp.unlink()
    commit_push_safe(f"Delete {data['path']}")
    return jsonify(status="success", path=data["path"])  

@app.get("/tree")
@handle_errors
def tree():
    files = []
    for p in LOCAL_FOLDER.rglob("*"):
        if p.is_file() and not p.name.startswith('.'):
            files.append(str(p.relative_to(LOCAL_FOLDER)))
    files.sort()
    return jsonify(files=files, count=len(files))

@app.get("/profiles")
@handle_errors
def profiles():
    profiles = []
    for f in PROFILE_PATH.parent.glob("*.json"):
        try:
            j = json.loads(f.read_text())
            if 'name' in j:
                profiles.append(j['name'])
        except:
            continue
    profiles.sort()
    return jsonify(profiles=profiles)

@app.post("/profiles/activate")
@handle_errors
def activate_profile():
    data = request.get_json(force=True)
    if 'name' not in data:
        return jsonify(error="Missing required: name"), 400
    target = None
    for f in PROFILE_PATH.parent.glob("*.json"):
        try:
            j = json.loads(f.read_text())
            if j.get('name') == data['name']:
                target = f
                break
        except:
            continue
    if not target:
        return jsonify(error="Profile not found"), 404
    backup = PROFILE_PATH.with_suffix('.bak')
    shutil.copy2(PROFILE_PATH, backup)
    shutil.copy2(target, PROFILE_PATH)
    return jsonify(status="success", name=data['name'], message="Restart required")

@app.get("/health")
@handle_errors
def health():
    info = {"status": "ok", "repo": str(LOCAL_FOLDER), "safe_mode": SAFE_MODE}
    if not LOCAL_FOLDER.exists():
        info['status'] = 'error'
        info['message'] = 'Repo not found'
        return jsonify(info), 500
    try:
        st = safe_git_operation(["git", "status", "--porcelain"]).stdout
        info['git_status'] = 'clean' if not st.strip() else 'dirty'
        safe_git_operation(["git", "ls-remote", "origin"], timeout=10)
        info['remote'] = 'connected'
    except subprocess.CalledProcessError as e:
        info['status'] = 'warning'
        info['remote'] = 'disconnected'
        info['git_error'] = str(e)
    except subprocess.TimeoutExpired:
        info['status'] = 'warning'
        info['remote'] = 'timeout'
    code = 200 if info['status'] == 'ok' else 500
    return jsonify(info), code

@app.post("/verify_upload")
@handle_errors
def verify_upload():
    data = request.get_json(force=True)
    if 'path' not in data:
        return jsonify(error="Missing required: path"), 400
    p = validate_path(data['path'])
    exists = p.exists()
    res = {'exists': exists, 'path': str(p.relative_to(LOCAL_FOLDER))}
    if exists:
        st = p.stat()
        res.update(size=st.st_size, modified=st.st_mtime)
    return jsonify(res)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
