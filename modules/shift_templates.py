import streamlit as st
import pandas as pd
import requests
import io
import hashlib

# ======================================================
# HELPERS
# ======================================================
def to_bool(value):
    return str(value).strip().lower() == "true"


def is_blank(value):
    return value is None or str(value).strip() == "" or str(value).lower() == "null"


def parse_number(value):
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    v = str(value).strip()
    num = float(v)
    return int(num) if num.is_integer() else num


def js_number(value):
    if is_blank(value):
        return None
    return parse_number(value)


def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def format_time(value):
    """
    Accepts:
      - '01-01-1970 09:30'
      - '09:30'
    Returns:
      - '09:30'
    """
    v = str(value).strip()
    return v[-5:]


# ======================================================
# MAIN
# ======================================================
def shift_templates_ui():

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    uploaded_file = st.file_uploader("Upload Excel / CSV", ["xlsx", "xls", "csv"])

    if "processed_shift_hash" not in st.session_state:
        st.session_state.processed_shift_hash = None

    if not uploaded_file:
        return

    file_bytes = uploaded_file.getvalue()
    current_hash = file_hash(file_bytes)

    df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(io.BytesIO(file_bytes))
    ).fillna("")

    st.info(f"Rows detected: {len(df)}")

    if not st.button("🚀 Create Shifts", type="primary"):
        return

    if st.session_state.processed_shift_hash == current_hash:
        st.warning("⚠ This file was already processed")
        return

    st.session_state.processed_shift_hash = current_hash
    results = []

    for i, row in df.iterrows():
        try:
            # -------------------------------
            # PAYCODES
            # -------------------------------
            paycodes = []

            for x in range(1, 11):
                pc_id = row.get(f"paycode_id{x}")
                start = row.get(f"paycode_startMinute{x}")
                end = row.get(f"paycode_endMinute{x}")

                if is_blank(pc_id) or is_blank(start):
                    continue

                paycode = {
                    "startMinute": parse_number(start),
                    "paycode": {"id": parse_number(pc_id)}
                }

                if not is_blank(end):
                    paycode["endMinute"] = parse_number(end)

                paycodes.append(paycode)

            if not paycodes:
                raise Exception("At least one paycode is required")

            # enforce max logic
            for idx, pc in enumerate(paycodes):
                is_last = idx == len(paycodes) - 1
                if is_last or "endMinute" not in pc:
                    pc.pop("endMinute", None)
                    pc["max"] = True
                else:
                    pc["max"] = False

            # -------------------------------
            # PAYLOAD (NO EXCEPTIONS SENT)
            # -------------------------------
            payload = {
                "name": row["name"],
                "description": row["description"],
                "startTime": format_time(row["startTime"]),
                "endTime": format_time(row["endTime"]),

                "beforeStartToleranceMinute": js_number(row.get("beforeStartToleranceMinute")),
                "afterStartToleranceMinute": js_number(row.get("afterStartToleranceMinute")),
                "lateInToleranceMinute": js_number(row.get("lateInToleranceMinute")),
                "earlyOutToleranceMinute": js_number(row.get("earlyOutToleranceMinute")),

                "report": to_bool(row["report"]),

                "monday": to_bool(row["monday"]),
                "tuesday": to_bool(row["tuesday"]),
                "wednesday": to_bool(row["wednesday"]),
                "thursday": to_bool(row["thursday"]),
                "friday": to_bool(row["friday"]),
                "saturday": to_bool(row["saturday"]),
                "sunday": to_bool(row["sunday"]),

                "paycodes": paycodes
            }

            r = requests.post(BASE_URL, headers=headers, json=payload)

            if r.status_code not in (200, 201):
                raise Exception(f"{r.status_code}: {r.text}")

            results.append({
                "Row": i + 1,
                "Name": row["name"],
                "Status": "Success"
            })

        except Exception as e:
            results.append({
                "Row": i + 1,
                "Name": row.get("name"),
                "Status": "Failed",
                "Message": str(e)
            })

    st.dataframe(pd.DataFrame(results), use_container_width=True)
