import streamlit as st
import requests

def render_profile_panel(api_url: str, log_message):
    st.sidebar.markdown("### Profile")
    try:
        prof_resp = requests.get(f"{api_url}/profiles", timeout=5)
        prof_resp.raise_for_status()
        profiles = prof_resp.json().get("profiles", [])
    except Exception as exc:
        st.sidebar.error(f"Could not fetch profile list: {exc}")
        return

    if "active_profile" not in st.session_state:
        # call `/` once to know the active profile
        try:
            idx = requests.get(api_url, timeout=5).json()
            st.session_state.active_profile = idx.get("active_profile", "")
        except Exception:
            st.session_state.active_profile = ""

    active = st.session_state.get("active_profile", "")

    for prof in profiles:
        label = f"**{prof}**" if prof == active else prof
        if st.sidebar.button(label, key=f"profile_{prof}"):
            try:
                requests.post(f"{api_url}/profiles/activate",
                              json={"name": prof}, timeout=5).raise_for_status()
                log_message(f"Switched to profile: {prof}")
                st.experimental_rerun()
            except Exception as exc:
                st.sidebar.error(f"Activation failed: {exc}")