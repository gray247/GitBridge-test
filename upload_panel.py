import streamlit as st
import requests

def render_upload_panel(api_url, log_message):
    st.header("Upload a File")
    with st.form("upload_form"):
        upload_path = st.text_input("File Path", value="demo/example.txt", key="upload_path")
        upload_content = st.text_area("Content", value="This is a test file.", key="upload_content")
        upload_submit = st.form_submit_button("Upload")
        if upload_submit:
            try:
                res = requests.post(f"{api_url}/upload", json={
                    "path": upload_path,
                    "content": upload_content
                })
                st.success(res.json())
                log_message(f"Uploaded: {upload_path}")
            except Exception as e:
                st.error(f"Upload failed: {e}")
                log_message(f"Upload failed: {upload_path}")