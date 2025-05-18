import streamlit as st
import requests
import json

def upload_file(api_url):
    st.header("Upload a File")
    with st.form("upload_form"):
        upload_path = st.text_input("File Path", value="demo/example.txt")
        upload_content = st.text_area("Content", value="This is a test file.")
        submitted = st.form_submit_button("Upload")
        if submitted:
            try:
                res = requests.post(f"{api_url}/upload", json={
                    "path": upload_path,
                    "content": upload_content
                })
                st.json(res.json())
            except Exception as e:
                st.error(f"Request failed: {e}")