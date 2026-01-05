import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime

# ======================================================
# DATE NORMALIZATION
# ======================================================
def normalize_yyyy_mm_dd(value):
    if not value:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    value = str(value).strip()
    if " " in value:
        value = value.split(" ")[0]
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


# ======================================================
# MAIN UI
# ======================================================
def paycode_events_ui():
    st.header("🧾 Paycode Events")

    HOST = st.session_state.HOST.rstrip("/")
    BASE_URL = f"{HOST}/resource-server/api/paycode_events"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
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
            pd.DataFrame(r.json())[["id", "code", "description"]]
            if r.status_code == 200 else pd.DataFrame()
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode Events")
            paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            output.getvalue(),
            "paycode_events_template.xlsx"
        )

    # ==================================================
    # UPLOAD
    # ==================================================
    st.subheader("📤 Upload Paycode Events")

    uploaded_file = st.file_uploader("Upload CSV / Excel", ["csv", "xlsx", "xls"])

    if not uploaded_file:
        return

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    ).fillna("")

    store = {}
    errors = []

    for idx, row in df.iterrows():
        raw_id = str(row.get("id", "")).strip()
        name = str(row.get("Paycode Event Name", "")).strip()
        description = str(row.get("Description", "")).strip() or name
        paycode_id = str(row.get("paycode_id", "")).strip()
        holiday_name = str(row.get("holiday_name", "")).strip()
        holiday_raw = row.get("holiday_date(YYYY-MM-DD)", "")

        repeat_week = str(row.get("repeatWeek", "")).strip() or "*"
        repeat_weekday = str(row.get("repeatWeekday", "")).strip() or "*"

        if not name or not holiday_name or not holiday_raw or not paycode_id:
            errors.append(f"Row {idx+1}: Missing mandatory fields")
            continue

        holiday_date = normalize_yyyy_mm_dd(holiday_raw)
        if not holiday_date:
            errors.append(f"Row {idx+1}: Invalid date {holiday_raw}")
            continue

        year, month, day = map(int, holiday_date.split("-"))

        # 🔐 CRITICAL FIX: GROUP BY ID IF PRESENT
        if raw_id.isdigit():
            key = f"ID_{raw_id}"
        else:
            key = f"NEW_{name}"

        if key not in store:
            payload = {
                "name": name,
                "description": description,
                "paycode": {"id": int(float(paycode_id))},
                "schedules": []
            }
            if raw_id.isdigit():
                payload["id"] = int(raw_id)

            store[key] = payload

        store[key]["schedules"].append({
            "name": holiday_name,
            "startDate": st.session_state.get("START_DATE", "2026-01-01"),
            "repeatYear": year,
            "repeatMonth": month,
            "repeatDay": day,
            "repeatWeek": repeat_week,
            "repeatWeekday": repeat_weekday
        })

    st.session_state.final_body = list(store.values())

    if errors:
        st.error("❌ Some rows were skipped")
        st.text("\n".join(errors))

    st.success(f"Loaded {len(store)} Paycode Events")

    # ==================================================
    # SUBMIT
    # ==================================================
    st.subheader("🚀 Create / Update Paycode Events")

    if not st.button("Submit Paycode Events"):
        return

    results = []

    for payload in st.session_state.final_body:
        is_update = isinstance(payload.get("id"), int)

        if is_update:
            r = requests.put(
                f"{BASE_URL}/{payload['id']}",
                headers=headers,
                json=payload
            )
        else:
            r = requests.post(BASE_URL, headers=headers, json=payload)

        results.append({
            "Paycode Event": payload["name"],
            "Action": "UPDATE" if is_update else "CREATE",
            "HTTP": r.status_code,
            "Status": "Success" if r.status_code in (200, 201) else "Failed"
        })

    st.dataframe(pd.DataFrame(results), use_container_width=True)
