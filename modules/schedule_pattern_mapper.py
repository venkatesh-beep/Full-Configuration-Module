import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import calendar

EMP_API = "/resource-server/api/employees"
TIMECARD_API = "/web-client/restProxy/timecards/"


# -------------------------------------------------------
# SESSION SANITIZER (VERY IMPORTANT)
# -------------------------------------------------------
def init_rules():
    if "rules" not in st.session_state:
        st.session_state.rules = []
    else:
        cleaned = []
        for r in st.session_state.rules:
            if isinstance(r, dict) and "Location" in r:
                cleaned.append(r)
        st.session_state.rules = cleaned


# -------------------------------------------------------
# API HELPERS
# -------------------------------------------------------
def get_employee_id(ext, date, headers, host):
    r = requests.get(
        f"{host}{TIMECARD_API}",
        headers=headers,
        params={"startDate": date, "endDate": date, "externalNumber": ext},
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
# UI PARITY LOGIC (same like assignments)
# -------------------------------------------------------
def apply_schedule_logic(emp, start_date, pattern_id, mode):
    new_start = datetime.strptime(start_date, "%Y-%m-%d")

    emp["login"]["confirmPassword"] = emp["login"]["password"]

    patterns = emp.get("schedulePatterns", [])
    patterns.sort(key=lambda x: datetime.strptime(x["startDate"], "%Y-%m-%d"))

    past = [p for p in patterns if datetime.strptime(p["startDate"], "%Y-%m-%d") < new_start]
    new_patterns = []

    if len(past) > 1:
        new_patterns.extend(past[:-1])

    if past:
        last = past[-1]
        last["endDate"] = (new_start - timedelta(days=1)).strftime("%Y-%m-%d")
        last["forever"] = False
        new_patterns.append(last)

    new_pattern = {
        "startDate": start_date,
        "schedulePattern": {"id": int(pattern_id)},
    }

    if mode == "FOREVER":
        new_pattern["forever"] = True
    else:
        last_day = calendar.monthrange(new_start.year, new_start.month)[1]
        new_pattern["endDate"] = datetime(
            new_start.year, new_start.month, last_day
        ).strftime("%Y-%m-%d")
        new_pattern["forever"] = False

    new_patterns.append(new_pattern)
    emp["schedulePatterns"] = new_patterns
    return emp


# -------------------------------------------------------
# MAIN UI
# -------------------------------------------------------
def schedule_pattern_mapper_ui():
    init_rules()

    st.header("🧠 Schedule Pattern Rule Engine")

    token = st.session_state.token
    host = st.session_state.HOST.rstrip("/")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # ---------------------------------------------------
    # RULE CREATION
    # ---------------------------------------------------
    st.subheader("1️⃣ Define Rules")

    c1, c2, c3, c4, c5 = st.columns(5)
    location = c1.text_input("Location")
    function = c2.text_input("Function")
    category = c3.text_input("Category")
    pattern = c4.text_input("Pattern ID")
    mode = c5.selectbox("Mode", ["ONE_MONTH", "FOREVER"])

    if st.button("Add Rule"):
        st.session_state.rules.append(
            {
                "Location": location.strip(),
                "Function": function.strip(),
                "Category": category.strip(),
                "Pattern": pattern.strip(),
                "Mode": mode,
            }
        )

    # ---------------------------------------------------
    # SHOW RULES + DELETE
    # ---------------------------------------------------
    if st.session_state.rules:
        st.markdown("### 🗂️ Current Rules")

        for idx, rule in enumerate(st.session_state.rules):
            col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,1,1,1])
            col1.write(rule["Location"])
            col2.write(rule["Function"])
            col3.write(rule["Category"])
            col4.write(rule["Pattern"])
            col5.write(rule["Mode"])
            if col6.button("❌", key=f"del{idx}"):
                st.session_state.rules.pop(idx)
                st.rerun()

    st.divider()

    # ---------------------------------------------------
    # HIRE DATE FROM UI
    # ---------------------------------------------------
    st.subheader("2️⃣ Hire Date")
    hire_date = st.date_input("Select Hire Date")
    hire_date_str = hire_date.strftime("%Y-%m-%d")

    st.divider()

    # ---------------------------------------------------
    # FILE UPLOAD
    # ---------------------------------------------------
    st.subheader("3️⃣ Upload HR File")
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file and st.button("🚀 Apply Schedule Mapping"):
        df = pd.read_excel(file)

        for _, row in df.iterrows():
            emp_no = str(row["Employee No."]).strip()
            emp_location = str(row["Location"]).strip()
            emp_function = str(row["Function"]).strip()
            emp_category = str(row["Category"]).strip()

            # find matching rule
            matched = None
            for rule in st.session_state.rules:
                if (
                    rule["Location"] in emp_location
                    and rule["Function"] in emp_function
                    and rule["Category"] in emp_category
                ):
                    matched = rule
                    break

            if not matched:
                st.warning(f"No rule for {emp_no}")
                continue

            emp_id = get_employee_id(emp_no, hire_date_str, headers, host)
            emp = get_employee(emp_id, headers, host)

            emp = apply_schedule_logic(
                emp,
                hire_date_str,
                matched["Pattern"],
                matched["Mode"],
            )

            put_employee(emp_id, emp, headers, host)
            st.success(f"✅ Updated {emp_no}")

        st.success("🎉 All Done")
