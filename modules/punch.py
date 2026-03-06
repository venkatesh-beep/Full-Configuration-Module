import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from modules.ui_helpers import module_header, section_header


# ----------------- HELPERS -----------------
def normalize_datetime(val: str) -> str:
    """
    Expect yyyy-mm-dd hh:mm:ss
    """
    val = str(val).strip()
    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")


# ----------------- UI -----------------
def punch_ui():
    module_header("🕒 Punch Update", "Add or bulk upload employee punches")

    st.divider()

    # ===== AUTH CHECK =====
    token = st.session_state.get("token")
    if not token:
        st.error("❌ Not logged in")
        st.stop()

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/punches/action/"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/json"
    }

    tab1, tab2 = st.tabs(["➕ Single Punch", "📤 Bulk Punch Upload"])

    # ======================================================
    # SINGLE PUNCH
    # ======================================================
    with tab1:
        section_header("➕ Add Single Punch")

        with st.container(border=True):
            c1, c2, c3 = st.columns(3)

            with c1:
                external_number = st.text_input(
                    "External Number",
                    placeholder="475087"
                )

            with c2:
                punch_date = st.text_input(
                    "Punch Date (YYYY-MM-DD)",
                    placeholder="2026-01-20"
                )

            with c3:
                punch_time = st.text_input(
                    "Punch Time (HH:MM:SS)",
                    placeholder="09:00:00"
                )

            st.markdown("")

            if st.button("✅ Submit Punch", use_container_width=True):
                if not external_number or not punch_date or not punch_time:
                    st.error("❌ All fields are mandatory")
                    st.stop()

                try:
                    punch_datetime = normalize_datetime(
                        f"{punch_date} {punch_time}"
                    )
                except Exception:
                    st.error("❌ Invalid date/time format")
                    st.stop()

                payload = {
                    "action": "ADD_NO_TYPE",
                    "punch": {
                        "employee": {
                            "externalNumber": external_number
                        },
                        "punchTime": punch_datetime
                    }
                }

                r = requests.post(
                    BASE_URL,
                    json=payload,
                    headers=headers,
                    verify=False
                )

                if r.status_code == 200:
                    st.success(f"✅ Punch added at {punch_datetime}")
                else:
                    st.error(f"❌ Failed ({r.status_code})")
                    try:
                        st.json(r.json())
                    except Exception:
                        st.write(r.text)

    # ======================================================
    # BULK PUNCH
    # ======================================================
    with tab2:
        section_header("📤 Bulk Punch Upload")

        with st.container(border=True):
            st.markdown(
                """
                **Required Excel format**

                | externalNumber | dateTime |
                |---------------|----------|
                | 475087        | 2026-01-20 09:00:00 |
                """
            )

            # -------- TEMPLATE DOWNLOAD --------
            template_df = pd.DataFrame(
                columns=["externalNumber", "dateTime"]
            )
            template_buffer = BytesIO()
            template_df.to_excel(template_buffer, index=False)
            template_buffer.seek(0)

            st.download_button(
                "⬇ Download Excel Template",
                data=template_buffer,
                file_name="punch_template.xlsx",
                use_container_width=True
            )

        st.divider()

        file = st.file_uploader(
            "Upload Filled Excel File",
            type=["xlsx"]
        )

        if file:
            df = pd.read_excel(file)

            section_header("👀 Preview")
            st.dataframe(df, use_container_width=True)

            required_cols = {"externalNumber", "dateTime"}
            if not required_cols.issubset(df.columns):
                st.error("❌ Excel must contain: externalNumber, dateTime")
                st.stop()

            if st.button("🚀 Upload Punches", use_container_width=True):
                success, failed = 0, 0
                results = []

                with st.spinner("Uploading punches..."):
                    for _, row in df.iterrows():
                        try:
                            punch_datetime = normalize_datetime(row["dateTime"])

                            payload = {
                                "action": "ADD_NO_TYPE",
                                "punch": {
                                    "employee": {
                                        "externalNumber": str(row["externalNumber"])
                                    },
                                    "punchTime": punch_datetime
                                }
                            }

                            r = requests.post(
                                BASE_URL,
                                json=payload,
                                headers=headers,
                                verify=False
                            )

                            if r.status_code == 200:
                                success += 1
                                results.append({
                                    "externalNumber": row["externalNumber"],
                                    "punchTime": punch_datetime,
                                    "status": "SUCCESS"
                                })
                            else:
                                failed += 1
                                results.append({
                                    "externalNumber": row["externalNumber"],
                                    "punchTime": punch_datetime,
                                    "status": f"FAILED ({r.status_code})"
                                })

                        except Exception as e:
                            failed += 1
                            results.append({
                                "externalNumber": row.get("externalNumber"),
                                "punchTime": row.get("dateTime"),
                                "status": str(e)
                            })

                results_df = pd.DataFrame(results)

                section_header("📊 Upload Summary")
                c1, c2, c3 = st.columns(3)
                c1.metric("📄 Total", len(results))
                c2.metric("✅ Uploaded", success)
                c3.metric("❌ Failed", failed)

                st.divider()

                st.dataframe(results_df, use_container_width=True)

                out = BytesIO()
                results_df.to_excel(out, index=False)
                out.seek(0)

                st.download_button(
                    "⬇ Download Result Report",
                    data=out,
                    file_name="punch_upload_results.xlsx",
                    use_container_width=True
                )
