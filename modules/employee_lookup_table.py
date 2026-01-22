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
    # HELPER: EXTRACT DATA + ORDER COLUMNS
    # ==================================================
    def extract_and_order(raw):
        # -------- Extract rows --------
        if isinstance(raw, list):
            data = raw
            ordered_cols = None
        elif isinstance(raw, dict):
            if "content" in raw:
                data = raw.get("content", [])
            elif "data" in raw:
                data = raw.get("data", [])
            else:
                data = []

            # -------- Column order from headers --------
            headers_meta = raw.get("headers", [])
            headers_meta = sorted(
                headers_meta,
                key=lambda x: x.get("sequence", 999)
            )

            ordered_cols = [
                h.get("data")
                for h in headers_meta
                if h.get("data")
            ]
        else:
            data = []
            ordered_cols = None

        if not data:
            return None, None

        df = pd.json_normalize(data)

        # -------- Apply column order --------
        if ordered_cols:
            existing_cols = [c for c in ordered_cols if c in df.columns]
            remaining_cols = [c for c in df.columns if c not in existing_cols]
            df = df[existing_cols + remaining_cols]

        return df, ordered_cols

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    if st.button("⬇️ Download Template", use_container_width=True):
        with st.spinner("Fetching employee lookup data..."):

            r = requests.get(API_URL, headers=headers, timeout=30)

            if r.status_code != 200:
                st.error("❌ Failed to fetch employee lookup data")
                return

            raw = r.json()
            df, ordered_cols = extract_and_order(raw)

            if df is None:
                st.warning("No data available in employee lookup table")
                return

            # Sheet 1: headers only
            template_df = pd.DataFrame(columns=df.columns)

            # Sheet 2: existing data
            existing_df = df.copy()

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                template_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Template"
                )
                existing_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Existing_Data"
                )

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
                return

            raw = r.json()
            df, _ = extract_and_order(raw)

            if df is None:
                st.warning("No data available to download")
                return

            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="employee_lookup_data.csv",
                mime="text/csv"
            )
