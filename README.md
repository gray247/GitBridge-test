# GitBridge

**GitBridge** is a lightweight Flask-based API for managing GitHub repositories remotely. It supports:

* **File upload** (`/upload`)
* **File move** (`/move`)
* **File delete** (`/delete`, when safe-mode is off)
* **Repository tree listing** (`/tree`)
* **Profile management** (`/profiles`, `/profiles/activate`)
* **Health check** (`/health`)
* **Upload verification** (`/verify_upload`)

This README will help you get started without a local CLI—everything can be tested via HTTP.

---

## 1. Prerequisites

* Python 3.11+
* A GitHub Personal Access Token (`repo` scope)
* A GitHub repository (e.g. `owner/repo`)

---

## 2. Profile Configuration

Create a directory `profiles/` in your project root and add a file named `active.json`:

```json
{
  "name": "default",
  "repo": "<owner/repo>",
  "token": "<YOUR_GITHUB_PAT>",
  "local_folder": "local_repo",
  "safe_mode": false
}
```

* **repo**: your GitHub `owner/repo`
* **token**: your Personal Access Token (or leave empty to use `GITHUB_TOKEN` env-var)
* **local\_folder**: where the repo will be cloned on disk
* **safe\_mode**: `true` to disable `/delete`

---

## 3. Environment Variables

Optionally, set these instead of (or in addition to) `active.json`:

```bash
export GITHUB_TOKEN="<YOUR_GITHUB_PAT>"
export GITBRIDGE_SAFE_MODE=false
```

* **GITHUB\_TOKEN**: overrides `token` in `active.json`
* **GITBRIDGE\_SAFE\_MODE**: overrides `safe_mode`

---

## 4. Installation & Startup

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:

   ```bash
   python gitbridge.py
   ```
3. By default, it listens on port **8080**.

> **Note:** On services like Render without a CLI, you configure environment variables in the dashboard and redeploy. Use the web UI or an API client (Postman, HTTPie, `curl`) to exercise the endpoints.

---

## 5. Testing Endpoints (via `curl`)

### 5.1 Health Check

```bash
curl https://<YOUR_URL>/health
```

Expect:

```json
{ "status": "ok", "repo": "/path/to/local_repo", "git_status": "clean", "remote": "connected", "safe_mode": false }
```

### 5.2 Upload File

```bash
curl -X POST https://<YOUR_URL>/upload \
  -H "Content-Type: application/json" \
  -d '{"path":"demo/hello.txt","content":"Hello, GitBridge!"}'
```

Expected response:

```json
{"status":"success","path":"demo/hello.txt"}
```

### 5.3 Verify Upload

```bash
curl -X POST https://<YOUR_URL>/verify_upload \
  -H "Content-Type: application/json" \
  -d '{"path":"demo/hello.txt"}'
```

Expected:

```json
{"exists":true,"path":"demo/hello.txt","size":123,"modified":1685200000.0}
```

### 5.4 Move File

```bash
curl -X POST https://<YOUR_URL>/move \
  -H "Content-Type: application/json" \
  -d '{"src":"demo/hello.txt","dst":"archive/hello.txt"}'
```

### 5.5 Delete File

> Only works if `safe_mode: false`

```bash
curl -X POST https://<YOUR_URL>/delete \
  -H "Content-Type: application/json" \
  -d '{"path":"archive/hello.txt"}'
```

### 5.6 List Repo Tree

```bash
curl https://<YOUR_URL>/tree
```

### 5.7 Profiles

* **List** available profiles:

  ```bash
  curl https://<YOUR_URL>/profiles
  ```
* **Activate** a profile:

  ```bash
  curl -X POST https://<YOUR_URL>/profiles/activate \
    -H "Content-Type: application/json" \
    -d '{"name":"default"}'
  ```

---

## 6. Next Steps

* Integrate a GUI or script to drive these endpoints.
* Monitor `gitbridge.log` for detailed logs.
* Consider splitting frontend/backend into separate services if you add a Streamlit UI.

---

You’re now ready to start using GitBridge. Just hit these endpoints from wherever you like—no local CLI needed!
