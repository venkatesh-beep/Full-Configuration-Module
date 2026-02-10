import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

from modules.ui_helpers import module_header, section_header


# ----------------- HELPERS -----------------
def normalize_date(val: str) -> str:
    """
    Expect yyyy-mm-dd
    """
    val = str(val).strip()
    return datetime.strptime(val, "%Y-%m-%d").strftime("%Y-%m-%d")


def parse_version(val) -> int:
    if val is None or str(val).strip() == "":
        return 0
    return int(val)


# ----------------- UI -----------------
def schedule_delete_ui():
    module_header("🗑️ Schedule Delete", "Delete single or bulk employee schedules")

    st.divider()

    # ===== AUTH CHECK =====
    token = st.session_state.get("token")
    if not token:
        st.error("❌ Not logged in")
        st.stop()

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/schedules/action"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/json"
    }

    tab1, tab2 = st.tabs(["➖ Single Delete", "📤 Bulk Delete Upload"])

    # ======================================================
    # SINGLE DELETE
    # ======================================================
    with tab1:
        section_header("➖ Delete Single Schedule")

        with st.container(border=True):
            c1, c2, c3 = st.columns(3)

            with c1:
                schedule_date = st.text_input(
                    "Schedule Date (YYYY-MM-DD)",
                    placeholder="2026-02-02"
                )

            with c2:
                employee_id = st.text_input(
                    "Employee ID",
                    placeholder="276057"
                )

            with c3:
                version = st.text_input(
                    "Version",
                    value="0"
                )

            st.markdown("")

            if st.button("🗑️ Delete Schedule", use_container_width=True):
                if not schedule_date or not employee_id:
                    st.error("❌ Schedule Date and Employee ID are mandatory")
                    st.stop()

                try:
                    normalized_date = normalize_date(schedule_date)
                    parsed_employee_id = int(str(employee_id).strip())
                    parsed_version = parse_version(version)
                except Exception:
                    st.error("❌ Invalid input. Check date (YYYY-MM-DD), Employee ID, and Version")
                    st.stop()

                payload = {
                    "action": "DELETE",
                    "data": [
                        {
                            "scheduleDate": normalized_date,
                            "employee": {
                                "id": parsed_employee_id
                            },
                            "version": parsed_version
                        }
                    ]
                }

                r = requests.post(
                    BASE_URL,
                    json=payload,
                    headers=headers,
                    verify=False
                )

                if r.status_code == 200:
                    st.success(f"✅ Schedule deleted for employee {parsed_employee_id} on {normalized_date}")
                else:
                    st.error(f"❌ Failed ({r.status_code})")
                    try:
                        st.json(r.json())
                    except Exception:
                        st.write(r.text)

    # ======================================================
    # BULK DELETE
    # ======================================================
    with tab2:
        section_header("📤 Bulk Schedule Delete")

        with st.container(border=True):
            st.markdown(
                """
                **Required Excel format**

                | scheduleDate | employeeId | version |
                |--------------|------------|---------|
                | 2026-02-02   | 276057     | 0       |
                """
            )

            # -------- TEMPLATE DOWNLOAD --------
            template_df = pd.DataFrame(
                columns=["scheduleDate", "employeeId", "version"]
            )
            template_buffer = BytesIO()
            template_df.to_excel(template_buffer, index=False)
            template_buffer.seek(0)

            st.download_button(
                "⬇ Download Excel Template",
                data=template_buffer,
                file_name="schedule_delete_template.xlsx",
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

            required_cols = {"scheduleDate", "employeeId", "version"}
            if not required_cols.issubset(df.columns):
                st.error("❌ Excel must contain: scheduleDate, employeeId, version")
                st.stop()

            if st.button("🚀 Delete Schedules", use_container_width=True):
                success, failed = 0, 0
                results = []

                with st.spinner("Deleting schedules..."):
                    for _, row in df.iterrows():
                        try:
                            normalized_date = normalize_date(row["scheduleDate"])
                            parsed_employee_id = int(row["employeeId"])
                            parsed_version = parse_version(row["version"])

                            payload = {
                                "action": "DELETE",
                                "data": [
                                    {
                                        "scheduleDate": normalized_date,
                                        "employee": {
                                            "id": parsed_employee_id
                                        },
                                        "version": parsed_version
                                    }
                                ]
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
                                    "scheduleDate": normalized_date,
                                    "employeeId": parsed_employee_id,
                                    "version": parsed_version,
                                    "status": "SUCCESS"
                                })
                            else:
                                failed += 1
                                results.append({
                                    "scheduleDate": normalized_date,
                                    "employeeId": parsed_employee_id,
                                    "version": parsed_version,
                                    "status": f"FAILED ({r.status_code})"
                                })

                        except Exception as e:
                            failed += 1
                            results.append({
                                "scheduleDate": row.get("scheduleDate"),
                                "employeeId": row.get("employeeId"),
                                "version": row.get("version"),
                                "status": str(e)
                            })

                results_df = pd.DataFrame(results)

                section_header("📊 Delete Summary")
                c1, c2, c3 = st.columns(3)
                c1.metric("📄 Total", len(results))
                c2.metric("✅ Deleted", success)
                c3.metric("❌ Failed", failed)

                st.divider()

                st.dataframe(results_df, use_container_width=True)
