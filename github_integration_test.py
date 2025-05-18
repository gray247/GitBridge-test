#!/usr/bin/env python3
"""
End-to-end GitBridge → GitHub smoke test.

ENV:
  GH_TOKEN   – GitHub PAT with repo scope
  GH_REPO    – owner/repo  (e.g. gray247/GitBridge-test)
"""
import os, time, uuid, requests, sys

API      = "http://localhost:8080"
HEADERS  = {"Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}"}

OWNER, REPO = os.environ["GH_REPO"].split("/", 1)
GH_COMMITS  = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"

def must(ok, msg):
    print(f"   {'✅' if ok else '❌'} {msg}")
    if not ok: sys.exit(1)

def call(route, payload):
    r = requests.post(f"{API}{route}", json=payload, timeout=10)
    must(r.status_code == 200, f"{route} failed → {r.text}")

uid   = uuid.uuid4().hex[:8]
paths = {
    "upload": f"itest/{uid}.txt",
    "moved" : f"itest_moved/{uid}.txt",
}

print("1) /upload …")
call("/upload", {"path": paths["upload"], "content": "hello"})
print("2) /move …")
call("/move", {"src": paths["upload"], "dst": paths["moved"]})
print("3) /delete …")
call("/delete", {"path": paths["moved"]})

print("4) waiting for Git push …")
time.sleep(4)                    # short wait; gitbridge already pushed

need = {f"Upload {paths['upload']}",
        f"Move {paths['upload']} to {paths['moved']}",
        f"Delete {paths['moved']}"}

print("5) verify commits on GitHub …")
resp = requests.get(GH_COMMITS, headers=HEADERS, params={"per_page": 10})
resp.raise_for_status()

messages = {c["commit"]["message"] for c in resp.json()}
missing  = need - messages
must(not missing, f"Missing commit messages: {sorted(missing)}")
print("🎉  All expected commits present on GitHub")