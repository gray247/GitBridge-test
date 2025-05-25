import streamlit as st
from upload_panel import render_upload_panel
from move_panel import render_move_panel
from delete_panel import render_delete_panel
from profile_panel import render_profile_panel
from gui_tree import render_tree_panel

API_URL = "https://gitbridge-test-1.onrender.com"

def log_message(msg):
    if "log" not in st.session_state:
        st.session_state["log"] = []
    st.session_state["log"].append(msg)

def init_log():
    if "log" not in st.session_state:
        st.session_state["log"] = []

def display_log():
    st.sidebar.subheader("Log")
    for entry in st.session_state.get("log", []):
        st.sidebar.write(entry)

st.set_page_config(page_title="GitBridge", layout="wide")
st.title("GitBridge Control Panel")

init_log()
render_profile_panel(API_URL, log_message)
render_upload_panel(API_URL, log_message)
render_move_panel(API_URL, log_message)
render_delete_panel(API_URL, log_message, safe_mode=st.session_state.get("safe_mode", False))
render_tree_panel(API_URL, log_message)
display_log()
