#!/bin/bash

# Kill anything using ports 8080 (backend) or 8501 (GUI)
fuser -k 8080/tcp > /dev/null 2>&1
fuser -k 8501/tcp > /dev/null 2>&1

# Start the Flask backend in the background
python3 gitbridge.py &

# Wait 3 seconds to ensure backend launches before GUI
sleep 3

# Start the Streamlit GUI
streamlit run gui.py --server.port=8501 --server.enableXsrfProtection=false --server.enableCORS=false