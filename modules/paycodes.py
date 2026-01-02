import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# MAIN UI
# ======================================================
def paycodes_ui():
    st.header("🧾 Paycodes Configuration")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD UPLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "code",
        "description",
        "inactive",
        "absence",
        "schedule",
        "exception",
        "historical",
        "validateWithPaycodeEvent",
        "linkRegularizeInTimeCard",
        "linkTimeOffInTimeCard",
        "presentDays",
        "lopDays",
        "leaveDays",
        "woDays",
        "holDays",
        "payableDays",
        "otHours"
    ])

    if st.button("⬇️ Download Paycode Template"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycodes_upload_template.xlsx"
        )

    # ==================================================
    # UPLOAD PAYCODES
    # ==================================================
    st.subheader("📤 Upload Paycodes (Create / Update)")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        ["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )
        df = df.fillna("")

        results = []

        for row_no, row in df.iterrows():
            try:
                payload = {
                    "code": str(row.get("code")).strip(),
                    "description": str(row.get("description")).strip(),
                    "inactive": bool(row.get("inactive")),
                    "absence": bool(row.get("absence")),
                    "schedule": bool(row.get("schedule")),
                    "exception": bool(row.get("exception")),
                    "historical": bool(row.get("historical")),
                    "validateWithPaycodeEvent": bool(row.get("validateWithPaycodeEvent")),
                    "linkRegularizeInTimeCard": bool(row.get("linkRegularizeInTimeCard")),
                    "linkTimeOffInTimeCard": bool(row.get("linkTimeOffInTimeCard")),
                    "presentDays": float(row.get("presentDays") or 0),
                    "lopDays": float(row.get("lopDays") or 0),
                    "leaveDays": float(row.get("leaveDays") or 0),
                    "woDays": float(row.get("woDays") or 0),
                    "holDays": float(row.get("holDays") or 0),
                    "payableDays": float(row.get("payableDays") or 0),
                    "otHours": float(row.get("otHours") or 0)
                }

                raw_id = str(row.get("id")).strip()

                # -------- CREATE / UPDATE ----------
                if raw_id.isdigit():
                    r = requests.put(
                        f"{BASE_URL}/{int(raw_id)}",
                        headers=headers,
                        json=payload
                    )
                    action = "Update"
                else:
                    r = requests.post(
                        BASE_URL,
                        headers=headers,
                        json=payload
                    )
                    action = "Create"

                results.append({
                    "Row": row_no + 1,
                    "Code": payload["code"],
                    "Action": action,
                    "HTTP Status": r.status_code,
                    "Status": "Success" if r.status_code in (200, 201) else "Failed",
                    "Message": r.text
                })

            except Exception as e:
                results.append({
                    "Row": row_no + 1,
                    "Code": row.get("code"),
                    "Action": "Error",
                    "HTTP Status": "",
                    "Status": "Failed",
                    "Message": str(e)
                })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    # ==================================================
    # DELETE PAYCODES
    # ==================================================
    st.subheader("🗑️ Delete Paycodes")

    ids_input = st.text_input("Enter Paycode IDs (comma-separated)")

    if st.button("Delete Paycodes"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        for pid in ids:
            r = requests.delete(f"{BASE_URL}/{pid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Paycode ID {pid}")
            else:
                st.error(f"Failed to delete ID {pid} → {r.text}")

    # ==================================================
    # DOWNLOAD EXISTING PAYCODES
    # ==================================================
    st.subheader("⬇️ Download Existing Paycodes")

    if st.button("Download Existing Paycodes"):
        r = requests.get(BASE_URL, headers=headers)
        if r.status_code != 200:
            st.error("❌ Failed to fetch paycodes")
        else:
            df = pd.DataFrame(r.json())
            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="paycodes_export.csv"
            )
