import streamlit as st
import requests


def render_delete_panel(api_url: str, log_message, safe_mode: bool) -> None:
    """
    Delete-file panel shown in the GUI sidebar.
    """
    st.header("Delete a File")

    with st.form("delete_form"):
        delete_path = st.text_input(
            "Path to Delete",
            value="archive/example.txt",
            key="delete_path",
        )
        delete_submit = st.form_submit_button("Delete")

        if safe_mode:
            st.warning("Safe mode is ON. Deletion is disabled.")
            return

        if delete_submit:
            try:
                res = requests.post(f"{api_url}/delete", json={"path": delete_path})
                st.success(res.json())
                log_message(f"Deleted {delete_path}")
            except Exception as e:
                st.error(f"Delete failed: {e}")
                log_message(f"Delete failed: {delete_path}")