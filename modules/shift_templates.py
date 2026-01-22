import streamlit as st
import pandas as pd
import requests
import io
import hashlib

# ======================================================
# SAFE BOOLEAN PARSER
# ======================================================
def to_bool(value, default=False):
    if value is None or str(value).strip() == "":
        return default
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in ("true", "1", "yes", "y"):
        return True
    if v in ("false", "0", "no", "n"):
        return False
    return default


# ======================================================
# FILE HASH (PREVENT REPROCESS)
# ======================================================
def file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


# ======================================================
# MAIN UI (CREATE ONLY)
# ======================================================
def shift_templates_ui():
    st.header("🕒 Shift Templates")
    st.caption("Create Shift Templates (Create only – no update)")

    BASE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/shift_templates"
    PAYCODE_URL = st.session_state.HOST.rstrip("/") + "/resource-server/api/paycodes"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD CREATE TEMPLATE
    # ==================================================
    st.subheader("📥 Download Create Template")

    template_df = pd.DataFrame(columns=[
        # -------- BASIC --------
        "name",
        "description",
        "startTime",
        "endTime",
        "beforeStartToleranceMinute",
        "afterStartToleranceMinute",
        "lateInToleranceMinute",
        "earlyOutToleranceMinute",
        "report",

        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday",

        # -------- PAYCODES (5 slots) --------
        "paycode_id1", "paycode_startMinute1", "paycode_endMinute1",
        "paycode_id2", "paycode_startMinute2", "paycode_endMinute2",
        "paycode_id3", "paycode_startMinute3", "paycode_endMinute3",
        "paycode_id4", "paycode_startMinute4", "paycode_endMinute4",
        "paycode_id5", "paycode_startMinute5",

        # -------- EXCEPTIONS (2 slots) --------
        "exception_paycode_id1", "exception_type1", "exception_startMinute1", "exception_endMinute1",
        "exception_paycode_id2", "exception_type2", "exception_startMinute2",

        # -------- ADJUSTMENTS (2 slots) --------
        "adjustment_type_id1", "adjustment_startMinute1", "adjustment_endMinute1", "adjustment_amountMinute1",
        "adjustment_type_id2", "adjustment_startMinute2", "adjustment_amountMinute2",

        # -------- ROUNDINGS (2 slots) --------
        "rounding_startMinute1", "rounding_endMinute1", "rounding_roundMinute1",
        "rounding_startMinute2", "rounding_roundMinute2",

        # -------- OPTIONAL SHIFT --------
        "optionalShiftTemplateId"
    ])

    if st.button("⬇️ Download Create Template", use_container_width=True):
        paycodes_df = pd.DataFrame()
        try:
            r = requests.get(PAYCODE_URL, headers=headers)
            if r.status_code == 200:
                paycodes_df = pd.DataFrame([
                    {"id": p["id"], "code": p["code"], "description": p["description"]}
                    for p in r.json()
                ])
        except Exception:
            pass

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Template")
            if not paycodes_df.empty:
                paycodes_df.to_excel(writer, index=False, sheet_name="Paycodes_Master")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="shift_templates_create.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD & CREATE SHIFT TEMPLATES
    # ==================================================
    st.subheader("📤 Upload & Create Shift Templates")

    uploaded_file = st.file_uploader("Upload Excel / CSV", ["xlsx", "xls", "csv"])

    if "processed_shift_hash" not in st.session_state:
        st.session_state.processed_shift_hash = None

    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        current_hash = file_hash(file_bytes)

        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(io.BytesIO(file_bytes))
        ).fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Create Shifts", type="primary"):

            if st.session_state.processed_shift_hash == current_hash:
                st.warning("⚠ File already processed")
                return

            st.session_state.processed_shift_hash = current_hash
            results = []

            for i, row in df.iterrows():
                try:
                    # ---------------- PAYCODES ----------------
                    paycodes = []
                    for x in range(1, 6):
                        pc_id = row.get(f"paycode_id{x}")
                        start = row.get(f"paycode_startMinute{x}")
                        end = row.get(f"paycode_endMinute{x}")

                        if pc_id == "" or start == "":
                            continue

                        pc = {
                            "paycode": {"id": int(pc_id)},
                            "startMinute": int(start)
                        }
                        if end != "":
                            pc["endMinute"] = int(end)

                        paycodes.append(pc)

                    for idx, pc in enumerate(paycodes):
                        pc["max"] = idx == len(paycodes) - 1
                        if pc["max"]:
                            pc.pop("endMinute", None)

                    # ---------------- EXCEPTIONS ----------------
                    exceptions = []
                    for x in range(1, 3):
                        pc_id = row.get(f"exception_paycode_id{x}")
                        etype = row.get(f"exception_type{x}")
                        start = row.get(f"exception_startMinute{x}")
                        end = row.get(f"exception_endMinute{x}")

                        if pc_id == "" or etype == "" or start == "":
                            continue

                        ex = {
                            "paycode": {"id": int(pc_id)},
                            "type": etype,
                            "startMinute": int(start)
                        }
                        if end != "":
                            ex["endMinute"] = int(end)

                        exceptions.append(ex)

                    for idx, ex in enumerate(exceptions):
                        ex["max"] = idx == len(exceptions) - 1
                        if ex["max"]:
                            ex.pop("endMinute", None)

                    # ---------------- ADJUSTMENTS ----------------
                    adjustments = []
                    for x in range(1, 3):
                        atype = row.get(f"adjustment_type_id{x}")
                        start = row.get(f"adjustment_startMinute{x}")
                        end = row.get(f"adjustment_endMinute{x}")
                        amt = row.get(f"adjustment_amountMinute{x}")

                        if atype == "" or start == "" or amt == "":
                            continue

                        adj = {
                            "adjustmentType": {"id": int(atype)},
                            "startMinute": int(start),
                            "amountMinute": int(amt)
                        }
                        if end != "":
                            adj["endMinute"] = int(end)

                        adjustments.append(adj)

                    for idx, adj in enumerate(adjustments):
                        adj["max"] = idx == len(adjustments) - 1
                        if adj["max"]:
                            adj.pop("endMinute", None)

                    # ---------------- ROUNDINGS ----------------
                    roundings = []
                    for x in range(1, 3):
                        start = row.get(f"rounding_startMinute{x}")
                        end = row.get(f"rounding_endMinute{x}")
                        rnd = row.get(f"rounding_roundMinute{x}")

                        if start == "" or rnd == "":
                            continue

                        r = {
                            "startMinute": int(start),
                            "roundMinute": int(rnd)
                        }
                        if end != "":
                            r["endMinute"] = int(end)

                        roundings.append(r)

                    for idx, r in enumerate(roundings):
                        r["max"] = idx == len(roundings) - 1
                        if r["max"]:
                            r.pop("endMinute", None)

                    # ---------------- FINAL PAYLOAD ----------------
                    payload = {
                        "name": row["name"],
                        "description": row["description"],
                        "startTime": row["startTime"],
                        "endTime": row["endTime"],
                        "beforeStartToleranceMinute": int(row["beforeStartToleranceMinute"]),
                        "afterStartToleranceMinute": int(row["afterStartToleranceMinute"]),
                        "lateInToleranceMinute": int(row["lateInToleranceMinute"]),
                        "earlyOutToleranceMinute": int(row["earlyOutToleranceMinute"]),
                        "report": to_bool(row["report"]),
                        "monday": to_bool(row["monday"]),
                        "tuesday": to_bool(row["tuesday"]),
                        "wednesday": to_bool(row["wednesday"]),
                        "thursday": to_bool(row["thursday"]),
                        "friday": to_bool(row["friday"]),
                        "saturday": to_bool(row["saturday"]),
                        "sunday": to_bool(row["sunday"]),
                        "paycodes": paycodes,
                        "exceptions": exceptions,
                        "adjustments": adjustments,
                        "exceptionRoundings": roundings
                    }

                    if row.get("optionalShiftTemplateId") != "":
                        payload["optionalShiftTemplate"] = {
                            "id": int(row["optionalShiftTemplateId"])
                        }

                    r = requests.post(BASE_URL, headers=headers, json=payload)

                    results.append({
                        "Row": i + 1,
                        "Name": row["name"],
                        "HTTP Status": r.status_code,
                        "Status": "Success" if r.status_code in (200, 201) else "Failed",
                        "Message": r.text
                    })

                except Exception as e:
                    results.append({
                        "Row": i + 1,
                        "Name": row.get("name"),
                        "HTTP Status": "",
                        "Status": "Failed",
                        "Message": str(e)
                    })

            st.dataframe(pd.DataFrame(results), use_container_width=True)
