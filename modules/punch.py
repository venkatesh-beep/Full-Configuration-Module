import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO


# ----------------- HELPERS -----------------
def normalize_datetime(val):
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d %H:%M:%S")

    val = str(val).strip()
    try:
        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError("Invalid DateTime format. Use yyyy-mm-dd hh:mm:ss")


# ----------------- UI -----------------
def punch_ui():
    st.header("🕒 Punch Update")
    st.caption("Add or bulk upload employee punches")

    # 🔐 SAME LOGIC AS PAYCODES
    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/punches/action/"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    tab1, tab2 = st.tabs(["➕ Single Punch", "📤 Bulk Punch Upload"])

    # ======================================================
    # SINGLE PUNCH
    # ======================================================
    with tab1:
        st.subheader("Single Punch Update")

        col1, col2, col3 = st.columns(3)
        with col1:
            external_number = st.text_input("External Number")
        with col2:
            punch_date = st.date_input("Punch Date")
        with col3:
            punch_time = st.text_input("Punch Time (HH:MM:SS)", "09:00:00")

        if st.button("✅ Submit Punch", use_container_width=True):
            if not external_number or not punch_time:
                st.error("External Number and Time are mandatory")
                st.stop()

            try:
                punch_datetime = normalize_datetime(
                    f"{punch_date} {punch_time}"
                )
            except Exception as e:
                st.error(str(e))
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

            response = requests.post(
                BASE_URL,
                json=payload,
                headers=headers,
                verify=False
            )

            if response.status_code == 200:
                st.success(f"✅ Punch updated at {punch_datetime}")
            else:
                st.error(f"❌ Failed ({response.status_code})")
                try:
                    st.json(response.json())
                except Exception:
                    st.write(response.text)

    # ======================================================
    # BULK PUNCH
    # ======================================================
    with tab2:
        st.subheader("Bulk Punch Upload")

        # -------- TEMPLATE DOWNLOAD --------
        template_df = pd.DataFrame(columns=["externalNumber", "dateTime"])
        buffer = BytesIO()
        template_df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "⬇ Download Excel Template",
            data=buffer,
            file_name="punch_template.xlsx",
            use_container_width=True
        )

        st.divider()

        file = st.file_uploader("Upload Excel File", type=["xlsx"])

        if file:
            df = pd.read_excel(file)
            st.dataframe(df, use_container_width=True)

            if not {"externalNumber", "dateTime"}.issubset(df.columns):
                st.error("Excel must contain columns: externalNumber, dateTime")
                st.stop()

            if st.button("🚀 Upload Punches", use_container_width=True):
                results = []
                success = 0
                failed = 0

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

                # -------- SUMMARY --------
                st.markdown("### 📊 Upload Summary")
                c1, c2, c3 = st.columns(3)
                c1.metric("📄 Total", len(results))
                c2.metric("✅ Uploaded", success)
                c3.metric("❌ Failed", failed)

                st.divider()
                st.dataframe(results_df, use_container_width=True)

                # -------- RESULT DOWNLOAD --------
                out = BytesIO()
                results_df.to_excel(out, index=False)
                out.seek(0)

                st.download_button(
                    "⬇ Download Result Report",
                    data=out,
                    file_name="punch_upload_results.xlsx",
                    use_container_width=True
                )
