#!/bin/bash
# Kill any existing Streamlit or Python processes that may block port
fuser -k 8501/tcp > /dev/null 2>&1

# Start Streamlit GUI with stable port and no CORS/XSRF issues
streamlit run gui.py --server.port=8501 --server.enableXsrfProtection=false --server.enableCORS=false