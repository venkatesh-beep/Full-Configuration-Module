import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def employee_lookup_table_ui():
    st.header("👤 Employee Lookup Table")
    st.caption("Download template and existing employee lookup data")

    API_URL = (
        st.session_state.HOST.rstrip("/")
        + "/resource-server/api/employee_lookup_table"
    )

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    if st.button("⬇️ Download Template", use_container_width=True):
        with st.spinner("Fetching employee lookup data..."):

            r = requests.get(API_URL, headers=headers, timeout=30)

            if r.status_code != 200:
                st.error("❌ Failed to fetch employee lookup data")
                st.code(f"{r.status_code}\n{r.text}")
                return

            raw = r.json()

            # ---- SAFE EXTRACTION ----
            if isinstance(raw, list):
                data = raw
            elif isinstance(raw, dict):
                if "content" in raw and isinstance(raw["content"], list):
                    data = raw["content"]
                elif "data" in raw and isinstance(raw["data"], list):
                    data = raw["data"]
                else:
                    data = []
            else:
                data = []

            if not data:
                st.warning("No data available in employee lookup table")
                return

            df = pd.json_normalize(data)

            template_df = pd.DataFrame(columns=df.columns)
            existing_df = df.copy()

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                template_df.to_excel(writer, index=False, sheet_name="Template")
                existing_df.to_excel(writer, index=False, sheet_name="Existing_Data")

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="employee_lookup_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING DATA
    # ==================================================
    st.subheader("⬇️ Download Existing Employee Lookup Data")

    if st.button("Download Existing Data", use_container_width=True):
        with st.spinner("Downloading data..."):

            r = requests.get(API_URL, headers=headers, timeout=30)

            if r.status_code != 200:
                st.error("❌ Failed to fetch employee lookup data")
                st.code(f"{r.status_code}\n{r.text}")
                return

            raw = r.json()

            # ---- SAFE EXTRACTION ----
            if isinstance(raw, list):
                data = raw
            elif isinstance(raw, dict):
                if "content" in raw and isinstance(raw["content"], list):
                    data = raw["content"]
                elif "data" in raw and isinstance(raw["data"], list):
                    data = raw["data"]
                else:
                    data = []
            else:
                data = []

            if not data:
                st.warning("No data available to download")
                return

            df = pd.json_normalize(data)

            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="employee_lookup_data.csv",
                mime="text/csv"
            )
