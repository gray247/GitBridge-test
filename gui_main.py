gui_main.py

import streamlit as st from gui_upload import upload_panel from gui_move import move_panel from gui_delete import delete_panel from gui_tree import tree_panel from gui_log import init_log, log_message, display_log

st.set_page_config(page_title="GitBridge Control Panel", layout="wide") st.title("GitBridge Control Panel") st.markdown("Full-featured interface for managing your GitHub repo through GitBridge.")

Safe Mode Toggle

if "safe_mode" not in st.session_state: st.session_state.safe_mode = True

st.sidebar.title("Settings") st.session_state.safe_mode = st.sidebar.checkbox("Safe Mode (Prevents deletion)", value=True)

Init log state

init_log()

Upload panel

upload_panel(log_message)

Move panel

move_panel(log_message)

Delete panel

delete_panel(log_message)

Tree viewer

tree_panel(log_message)

Log viewer

display_log()

