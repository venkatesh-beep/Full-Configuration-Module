import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import calendar

EMP_API = "/resource-server/api/employees"
TIMECARD_API = "/web-client/restProxy/timecards/"


# ---------------- API ----------------
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


# ---------------- Schedule Logic ----------------
def apply_schedule(emp, start_date, pattern_id, mode):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    emp["login"]["confirmPassword"] = emp["login"]["password"]

    patterns = emp.get("schedulePatterns", [])
    patterns.sort(key=lambda x: x["startDate"])

    past = [p for p in patterns if p["startDate"] < start_date]
    new_patterns = []

    if len(past) > 1:
        new_patterns.extend(past[:-1])

    if past:
        last = past[-1]
        last["endDate"] = (start - timedelta(days=1)).strftime("%Y-%m-%d")
        last["forever"] = False
        new_patterns.append(last)

    new_p = {
        "startDate": start_date,
        "schedulePattern": {"id": int(pattern_id)},
    }

    if mode == "FOREVER":
        new_p["forever"] = True
    else:
        last_day = calendar.monthrange(start.year, start.month)[1]
        new_p["endDate"] = f"{start.year}-{start.month:02d}-{last_day}"
        new_p["forever"] = False

    new_patterns.append(new_p)
    emp["schedulePatterns"] = new_patterns
    return emp


# ---------------- UI ----------------
def schedule_pattern_mapper_ui():
    st.header("🧠 Schedule Pattern Rule Engine")

    token = st.session_state.token
    host = st.session_state.HOST.rstrip("/")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # ---------- RULE BUILDER ----------
    st.subheader("1️⃣ Define Rules")

    if "rules" not in st.session_state:
        st.session_state.rules = []

    c1, c2, c3, c4, c5 = st.columns(5)
    loc = c1.text_input("Location")
    func = c2.text_input("Function")
    cat = c3.text_input("Category")
    pat = c4.text_input("Pattern ID")
    mode = c5.selectbox("Mode", ["ONE_MONTH", "FOREVER"])

    if st.button("Add Rule"):
        st.session_state.rules.append((loc, func, cat, pat, mode))

    if st.session_state.rules:
        st.table(
            pd.DataFrame(
                st.session_state.rules,
                columns=["Location", "Function", "Category", "Pattern", "Mode"],
            )
        )

    # ---------- HIRE DATE ----------
    st.subheader("2️⃣ Hire Date")
    hire_date = st.date_input("Use this hire date for all")
    hire_date = hire_date.strftime("%Y-%m-%d")

    # ---------- FILE ----------
    st.subheader("3️⃣ Upload HR File")
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file and st.button("🚀 Run Mapping"):
        df = pd.read_excel(file)

        for _, row in df.iterrows():
            ext = str(row["Employee No."]).strip()
            location = str(row["Location"]).strip()
            function = str(row["Function"]).strip()
            category = str(row["Category"]).strip()

            # rule match
            rule = next(
                (
                    r
                    for r in st.session_state.rules
                    if r[0] == location
                    and r[1] == function
                    and r[2] == category
                ),
                None,
            )

            if not rule:
                st.warning(f"No rule → {ext}")
                continue

            _, _, _, pattern_id, mode = rule

            try:
                emp_id = get_employee_id(ext, hire_date, headers, host)
                emp = get_employee(emp_id, headers, host)
                emp = apply_schedule(emp, hire_date, pattern_id, mode)
                put_employee(emp_id, emp, headers, host)

                st.success(f"✅ {ext}")

            except Exception as e:
                st.error(f"{ext} → {e}")

        st.success("🎉 Completed")
