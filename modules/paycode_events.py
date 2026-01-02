import streamlit as st
import requests
import pandas as pd
import io
import re
from datetime import datetime

# ======================================================
# DATE NORMALIZATION (APPROVED LOGIC)
# ======================================================
def normalize_yyyy_mm_dd(date_value):
    if not date_value:
        return None

    if hasattr(date_value, "strftime"):
        return date_value.strftime("%Y-%m-%d")

    date_str = str(date_value).strip()

    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", date_str):
        return date_str.split(" ")[0]

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            return None

    return None


# ======================================================
# MAIN UI FUNCTION
# ======================================================
def paycode_events_ui():
    st.header("🧾 Paycode Events")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycode_events"
    PAYCODES_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "Paycode Event Name",
        "Description",
        "paycode_id",
        "holiday_name",
        "holiday_date(YYYY-MM-DD)",
        "repeatWeek",
        "repeatWeekday"
    ])

    if st.button("⬇️ Download Template"):
        r = requests.get(PAYCODES_URL, headers=headers)
        paycodes_df = (
            pd.DataFrame(r.json()) if r.status_code == 200
            else pd.DataFrame(columns=["id", "code"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode Events")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_events_template.xlsx"
        )

    # ==================================================
    # UPLOAD
    # ==================================================
    st.subheader("📤 Upload Paycode Events")

    uploaded_file = st.file_uploader("Upload CSV or Excel", ["csv", "xlsx", "xls"])

    if uploaded_file:
        store = {}
        errors = []

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )
        df = df.fillna("")

        for row_no, row in df.iterrows():
            raw_id = str(row.get("id", "")).strip()
            name = str(row.get("Paycode Event Name", "")).strip()
            description = str(row.get("Description", "")).strip() or name
            paycode_id = str(row.get("paycode_id", "")).strip()
            holiday_name = str(row.get("holiday_name", "")).strip()
            holiday_raw = row.get("holiday_date(YYYY-MM-DD)", "")

            repeat_week = str(row.get("repeatWeek", "")).strip() or "*"
            repeat_weekday = str(row.get("repeatWeekday", "")).strip() or "*"

            if not name or not holiday_name or not holiday_raw or not paycode_id:
                errors.append(f"Row {row_no + 1}: Missing mandatory fields")
                continue

            holiday_date = normalize_yyyy_mm_dd(holiday_raw)
            if not holiday_date:
                errors.append(
                    f"Row {row_no + 1}: Invalid date '{holiday_raw}' (Expected YYYY-MM-DD)"
                )
                continue

            year, month, day = map(int, holiday_date.split("-"))
            key = raw_id if raw_id.isdigit() else name

            if key not in store:
                base = {
                    "name": name,
                    "description": description,
                    "paycode": {"id": int(float(paycode_id))},
                    "schedules": []
                }
                if raw_id.isdigit():
                    base["id"] = int(raw_id)
                store[key] = base

            store[key]["schedules"].append({
                "name": holiday_name,
                "startDate": st.session_state.get("START_DATE", "2026-01-01"),
                "repeatDay": day,
                "repeatMonth": month,
                "repeatYear": year,
                "repeatWeek": repeat_week,
                "repeatWeekday": repeat_weekday
            })

        st.session_state.final_body = list(store.values())

        if errors:
            st.error("❌ Some rows were skipped")
            st.text("\n".join(errors))

        st.success(f"✅ Loaded {len(store)} Paycode Events")

    # ==================================================
    # CREATE / UPDATE
    # ==================================================
    st.subheader("🚀 Create / Update Paycode Events")

    if st.button("Submit Paycode Events"):
        results = []

        for payload in st.session_state.get("final_body", []):
            is_update = "id" in payload

            r = (
                requests.put(f"{BASE_URL}/{payload['id']}", headers=headers, json=payload)
                if is_update
                else requests.post(BASE_URL, headers=headers, json=payload)
            )

            results.append({
                "Paycode Event": payload["name"],
                "Action": "Update" if is_update else "Create",
                "HTTP Status": r.status_code,
                "Status": "Success" if r.status_code in (200, 201) else "Failed",
                "Message": r.text
            })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

    # ==================================================
    # DELETE
    # ==================================================
    st.subheader("🗑️ Delete Paycode Events")

    ids_input = st.text_input("Enter Paycode Event IDs (comma-separated)")
    if st.button("Delete Paycode Events"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]

        for pid in ids:
            r = requests.delete(f"{BASE_URL}/{pid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted Paycode Event ID {pid}")
            else:
                st.error(f"Failed to delete ID {pid} → {r.text}")

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Paycode Events")

    if st.button("Download Existing Paycode Events"):
        r = requests.get(BASE_URL, headers=headers)

        if r.status_code != 200:
            st.error("❌ Failed to fetch Paycode Events")
        else:
            rows = []

            for e in r.json():
                for s in e.get("schedules", []):
                    ry = s.get("repeatYear")
                    rm = s.get("repeatMonth")
                    rd = s.get("repeatDay")

                    holiday_date = ""
                    if str(ry).isdigit() and str(rm).isdigit() and str(rd).isdigit():
                        holiday_date = f"{int(ry):04d}-{int(rm):02d}-{int(rd):02d}"

                    rows.append({
                        "id": e.get("id"),
                        "Paycode Event Name": e.get("name"),
                        "Description": e.get("description"),
                        "paycode_id": e.get("paycode", {}).get("id"),
                        "holiday_name": s.get("name"),
                        "holiday_date(YYYY-MM-DD)": holiday_date,
                        "repeatWeek": s.get("repeatWeek", "*"),
                        "repeatWeekday": s.get("repeatWeekday", "*")
                    })

            df = pd.DataFrame(rows)
            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False),
                file_name="paycode_events_export.csv"
            )
