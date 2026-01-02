import streamlit as st
import pandas as pd
from services.api import get, post, put, delete

BASE = "/resource-server/api/paycodes"

def paycodes_ui():
    st.header("🧾 Paycodes")

    host = st.session_state.HOST.rstrip("/")
    url = host + BASE

    st.subheader("➕ Create / Update Paycode")

    with st.form("paycode_form"):
        pid = st.text_input("Paycode ID (blank = create)")
        code = st.text_input("Code")
        description = st.text_input("Description")
        submit = st.form_submit_button("Submit")

    if submit:
        body = {"code": code, "description": description}
        r = put(f"{url}/{pid}", body) if pid.isdigit() else post(url, body)
        st.success("Success" if r.status_code in (200, 201) else r.text)

    st.subheader("🗑️ Delete Paycode")
    did = st.text_input("Paycode ID")
    if st.button("Delete"):
        r = delete(f"{url}/{did}")
        st.success("Deleted" if r.status_code in (200, 204) else r.text)

    st.subheader("📥 Existing Paycodes")
    r = get(url)
    if r.status_code == 200:
        st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
