# GitBridge

GitBridge is a hands-off development tool that allows LLMs to programmatically manage your GitHub project files through a Streamlit GUI and Flask API.

## Features
- Upload, move, and delete files in your GitHub repo
- Profile switching
- Git auto-commit and push
- Streamlit GUI for easy control

## Setup

### 1. Install Dependencies
```bash
pip install flask streamlit requests
```

### 2. Start the Backend
```bash
python3 gitbridge.py
```

### 3. Run the GUI
```bash
streamlit run gui.py
```

### 4. Test GitHub Integration (optional)
```bash
python3 github_integration_test.py
```

Make sure `profiles/active.json` contains a valid GitHub token and repo name.

## Notes
- Safe mode prevents file deletion.
- Commits are pushed to the `main` branch by default.