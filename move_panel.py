import streamlit as st
import requests

def render_move_panel(api_url, log_message):
    st.header("Move a File")
    with st.form("move_form"):
        src = st.text_input("Source Path", value="demo/example.txt", key="move_src")
        dst = st.text_input("Destination Path", value="archive/example.txt", key="move_dst")
        move_submit = st.form_submit_button("Move")
        if move_submit:
            try:
                res = requests.post(f"{api_url}/move", json={
                    "src": src,
                    "dst": dst
                })
                st.success(res.json())
                log_message(f"Moved: {src} to {dst}")
            except Exception as e:
                st.error(f"Move failed: {e}")
                log_message(f"Move failed: {src} to {dst}")