#!/bin/bash
# Kill anything using port 8080 (Flask default)
fuser -k 8080/tcp > /dev/null 2>&1

# Start the GitBridge backend
python3 gitbridge.py