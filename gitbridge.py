#!/usr/bin/env python3
"""
GitBridge — minimal Flask backend that:
• clones / keeps a GitHub repo locally
• exposes /upload /move /delete /tree REST endpoints
• (NEW) guarantees we work on the repo’s default branch `main`
• (NEW) provides /profiles so the Streamlit GUI can list profile names
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------
# 0.  CONFIG / PROFILE
# ---------------------------------------------------------------------
PROFILE_PATH = Path("profiles/active.json")

if not PROFILE_PATH.exists():
    raise FileNotFoundError("Missing profile: profiles/active.json")

profile: Dict = json.loads(PROFILE_PATH.read_text())
REPO          = profile["repo"]          # e.g. "gray247/GitBridge-test"
TOKEN         = profile["token"]         # a classic PAT or fine-grained token
LOCAL_FOLDER  = Path(profile["local_folder"])
SAFE_MODE     = bool(profile.get("safe_mode", True))   # guard deletes

# ---------------------------------------------------------------------
# 1.  GIT SETUP (clone if first run, then ensure we're on `main`)
# ---------------------------------------------------------------------
if not LOCAL_FOLDER.exists():
    print("📥  Cloning repo …")
    subprocess.run(
        ["git", "clone", f"https://{TOKEN}@github.com/{REPO}.git", str(LOCAL_FOLDER)],
        check=True,
    )

# Always operate on / push to `main`
subprocess.run(["git", "checkout", "-B", "main"], cwd=LOCAL_FOLDER, check=True)

# ---------------------------------------------------------------------
# 2.  FLASK APP
# ---------------------------------------------------------------------
app = Flask(__name__)
print("🚀 GitBridge backend is starting …")
print(f"    repo   : {REPO}")
print(f"    folder : {LOCAL_FOLDER.resolve()}")
print(f"    safe   : {SAFE_MODE}")

# ---------------- helpers ----------------
def _write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit_push(msg: str) -> None:
    """Stage, commit and push to origin/main."""
    subprocess.run(["git", "add", "."], cwd=LOCAL_FOLDER, check=True)
    # allow “nothing to commit” without crashing
    subprocess.run(["git", "commit", "-m", msg], cwd=LOCAL_FOLDER)
    subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=LOCAL_FOLDER, check=True)


# ---------------- routes -----------------
@app.get("/")
def index():
    return jsonify(
        status="GitBridge is live",
        endpoints=["/upload", "/move", "/delete", "/tree", "/profiles"],
    )


@app.post("/upload")
def upload():
    data = request.get_json(force=True)
    if not data or "path" not in data or "content" not in data:
        return jsonify(error="Missing path or content"), 400

    full = LOCAL_FOLDER / data["path"]
    try:
        _write_file(full, data["content"])
        _commit_push(f"Upload {data['path']}")
        return jsonify(status="Uploaded", path=data["path"])
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=str(exc)), 500


@app.post("/move")
def move():
    data = request.get_json(force=True)
    if not data or "src" not in data or "dst" not in data:
        return jsonify(error="Missing src or dst"), 400

    src = LOCAL_FOLDER / data["src"]
    dst = LOCAL_FOLDER / data["dst"]
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        _commit_push(f"Move {data['src']} to {data['dst']}")
        return jsonify(status="Moved", from_=data["src"], to=data["dst"])
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=str(exc)), 500


@app.post("/delete")
def delete():
    data = request.get_json(force=True)
    if not data or "path" not in data:
        return jsonify(error="Missing path"), 400
    if SAFE_MODE:
        return jsonify(error="Deletion disabled (safe mode)"), 403

    full = LOCAL_FOLDER / data["path"]
    if not full.exists():
        return jsonify(error=f"File not found: {data['path']}"), 404
    try:
        full.unlink()
        _commit_push(f"Delete {data['path']}")
        return jsonify(status="Deleted", path=data["path"])
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=str(exc)), 500


@app.get("/tree")
def tree():
    files: List[str] = [
        str(p.relative_to(LOCAL_FOLDER)) for p in LOCAL_FOLDER.rglob("*") if p.is_file()
    ]
    return jsonify(files=sorted(files))


# --- NEW: lightweight profile lister for the GUI sidebar -------------
@app.get("/profiles")
def profiles():
    prof_dir = PROFILE_PATH.parent
    names = []
    for p in prof_dir.glob("*.json"):
        try:
            names.append(json.loads(p.read_text())["name"])
        except Exception:  # noqa: BLE001
            continue
    return jsonify(profiles=names)


# ---------------------------------------------------------------------
# 3.  RUN
# ---------------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify(status="ok")

@app.post("/verify_upload")
def verify_upload():
    data = request.get_json(force=True)
    path = LOCAL_FOLDER / data.get("path", "")
    return jsonify(exists=path.exists(), path=str(path))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)