import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import calendar

EMP_API = "/resource-server/api/employees"
TIMECARD_API = "/web-client/restProxy/timecards/"


# -------------------------------------------------------
# API HELPERS
# -------------------------------------------------------
def get_employee_id(external_number, date, headers, host):
    r = requests.get(
        f"{host}{TIMECARD_API}",
        headers=headers,
        params={
            "startDate": date,
            "endDate": date,
            "externalNumber": external_number
        }
    )
    r.raise_for_status()
    return r.json()[0]["entries"][0]["employee"]["id"]


def get_employee(emp_id, headers, host):
    r = requests.get(f"{host}{EMP_API}/{emp_id}?projection=FULL", headers=headers)
    r.raise_for_status()
    return r.json()


def put_employee(emp_id, emp, headers, host):
    r = requests.put(f"{host}{EMP_API}/{emp_id}", headers=headers, json=emp)
    r.raise_for_status()


# -------------------------------------------------------
# UI PARITY SCHEDULE LOGIC
# -------------------------------------------------------
def apply_schedule_logic(emp, start_date, pattern_id, mode):
    start = datetime.strptime(start_date, "%Y-%m-%d")

    emp["login"]["confirmPassword"] = emp["login"]["password"]

    patterns = emp.get("schedulePatterns", [])
    patterns.sort(key=lambda a: datetime.strptime(a["startDate"], "%Y-%m-%d"))

    past = [p for p in patterns if datetime.strptime(p["startDate"], "%Y-%m-%d") < start]
    new_patterns = []

    if len(past) > 1:
        new_patterns.extend(past[:-1])

    if past:
        last = past[-1]
        last["endDate"] = (start - timedelta(days=1)).strftime("%Y-%m-%d")
        last["forever"] = False
        new_patterns.append(last)

    new_pattern = {
        "startDate": start_date,
        "schedulePattern": {"id": int(pattern_id)}
    }

    if mode == "FOREVER":
        new_pattern["forever"] = True
    else:
        last_day = calendar.monthrange(start.year, start.month)[1]
        new_pattern["endDate"] = datetime(
            start.year, start.month, last_day
        ).strftime("%Y-%m-%d")
        new_pattern["forever"] = False

    new_patterns.append(new_pattern)
    emp["schedulePatterns"] = new_patterns
    return emp


# -------------------------------------------------------
# MAIN UI
# -------------------------------------------------------
def schedule_pattern_mapper_ui():
    st.header("🗓️ Smart Schedule Pattern Mapper")

    token = st.session_state.token
    host = st.session_state.HOST.rstrip("/")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    st.markdown("### 1️⃣ Define Mapping Rules (Location → Pattern → Mode)")

    if "rules" not in st.session_state:
        st.session_state.rules = []

    col1, col2, col3 = st.columns(3)

    with col1:
        location = st.text_input("Location Name (exact from Excel Column R)")
    with col2:
        pattern_id = st.text_input("Schedule Pattern ID")
    with col3:
        mode = st.selectbox("Mode", ["ONE_MONTH", "FOREVER"])

    if st.button("➕ Add Rule"):
        st.session_state.rules.append((location.strip(), pattern_id.strip(), mode))

    if st.session_state.rules:
        st.table(pd.DataFrame(
            st.session_state.rules,
            columns=["Location", "Pattern ID", "Mode"]
        ))

    st.divider()
    st.markdown("### 2️⃣ Select Hire Date")
    hire_date = st.date_input("Apply from Hire Date")
    hire_date_str = hire_date.strftime("%Y-%m-%d")

    st.divider()
    st.markdown("### 3️⃣ Upload HR File")

    file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

    if file and st.button("🚀 Apply Mapping"):
        df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)

        for _, row in df.iterrows():
            ext = str(row["Employee No."]).strip()
            emp_location = str(row["Location"]).strip()

            # Find matching rule
            rule = next((r for r in st.session_state.rules if r[0] == emp_location), None)

            if not rule:
                st.warning(f"No rule for location: {emp_location}")
                continue

            pattern_id, mode = rule[1], rule[2]

            try:
                emp_id = get_employee_id(ext, hire_date_str, headers, host)
                emp = get_employee(emp_id, headers, host)

                emp = apply_schedule_logic(emp, hire_date_str, pattern_id, mode)
                put_employee(emp_id, emp, headers, host)

                st.success(f"✅ {ext} → {emp_location}")

            except Exception as e:
                st.error(f"❌ {ext}: {e}")

        st.success("🎉 Mapping Completed")
