import streamlit as st
import requests
import json

def move_file(api_url):
    st.header("Move a File")
    with st.form("move_form"):
        src = st.text_input("Source Path", value="demo/example.txt")
        dst = st.text_input("Destination Path", value="archive/example.txt")
        submitted = st.form_submit_button("Move")
        if submitted:
            try:
                res = requests.post(f"{api_url}/move", json={"src": src, "dst": dst})
                st.json(res.json())
            except Exception as e:
                st.error(f"Request failed: {e}")