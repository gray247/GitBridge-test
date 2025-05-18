import streamlit as st
import requests

def render_tree_panel(api_url, log_message):
    st.header("View File Tree")
    if st.button("Refresh Tree"):
        try:
            res = requests.get(f"{api_url}/tree")
            files = res.json().get("files", [])
            st.code("\n".join(files))
            log_message("Refreshed file tree")
        except Exception as e:
            st.error(f"Tree fetch failed: {e}")
            log_message("Tree fetch failed")