#!/bin/bash

mkdir -p profiles

cat <<EOF > profiles/active.json
{
  "name": "GitBridge-test",
  "repo": "gray247/GitBridge-test",
  "token": "${GH_TOKEN}",
  "local_folder": "repo",
  "safe_mode": false
}
EOF

fuser -k 8080/tcp > /dev/null 2>&1
fuser -k 8501/tcp > /dev/null 2>&1

python3 core/main.py &
sleep 3
streamlit run gui.py --server.port=8501 --server.enableXsrfProtection=false --server.enableCORS=false
