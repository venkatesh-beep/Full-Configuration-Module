import streamlit as st
import pandas as pd
import requests
import io
import json

# ======================================================
# PAYCODE EVENT SETS UI
# ======================================================
def paycode_event_sets_ui():
    st.header("🧩 Paycode Event Sets")
    st.caption("Create, update, delete and download Paycode Event Sets")

    HOST = st.session_state.HOST.rstrip("/")
    SETS_URL = f"{HOST}/resource-server/api/paycode_event_sets"
    EVENTS_URL = f"{HOST}/resource-server/api/paycode_events"

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
        "id", "name", "description",
        "PaycodeEvent1", "Priority1",
        "PaycodeEvent2", "Priority2",
        "PaycodeEvent3", "Priority3",
        "PaycodeEvent4", "Priority4",
        "PaycodeEvent5", "Priority5"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        r = requests.get(EVENTS_URL, headers=headers)

        events_df = (
            pd.DataFrame([
                {"id": e["id"], "name": e["name"], "description": e["description"]}
                for e in r.json()
            ]) if r.status_code == 200 else
            pd.DataFrame(columns=["id", "name", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode_Event_Sets")
            events_df.to_excel(writer, index=False, sheet_name="Available_Paycode_Events")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_event_sets_template.xlsx"
        )

    st.divider()

    # ==================================================
    # UPLOAD
    # ==================================================
    st.subheader("📤 Upload Paycode Event Sets")

    uploaded_file = st.file_uploader("Upload CSV or Excel", ["csv", "xlsx", "xls"])

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):
            results = []

            with st.spinner("⏳ Processing Paycode Event Sets..."):
                for row_no, row in df.iterrows():
                    try:
                        raw_id = str(row.get("id", "")).strip()
                        name = str(row.get("name", "")).strip()
                        description = str(row.get("description", "")).strip() or name

                        if not name:
                            raise ValueError("Name is mandatory")

                        # ==============================
                        # BUILD ENTRIES FROM FILE
                        # ==============================
                        file_entries = []
                        for i in range(1, 6):
                            ev = row.get(f"PaycodeEvent{i}")
                            pr = row.get(f"Priority{i}")
                            if ev in ("", None):
                                continue
                            file_entries.append({
                                "paycodeEvent": {"id": int(float(ev))},
                                "priority": int(pr) if str(pr).isdigit() else i,
                                "overridable": False
                            })

                        # ==============================
                        # UPDATE
                        # ==============================
                        if raw_id.isdigit():
                            set_id = int(raw_id)

                            # 🔹 Fetch existing set
                            existing = requests.get(
                                f"{SETS_URL}/{set_id}", headers=headers
                            )

                            if existing.status_code != 200:
                                raise ValueError("Existing Paycode Event Set not found")

                            existing_json = existing.json()

                            payload = {
                                "id": set_id,
                                "name": name,
                                "description": description,
                                # 🔹 keep existing entries if file doesn't provide
                                "entries": file_entries if file_entries else existing_json.get("entries", [])
                            }

                            r = requests.put(
                                f"{SETS_URL}/{set_id}",
                                headers=headers,
                                json=payload
                            )
                            action = "Update"

                        # ==============================
                        # CREATE
                        # ==============================
                        else:
                            if not file_entries:
                                raise ValueError("Entries required for Create")

                            payload = {
                                "name": name,
                                "description": description,
                                "entries": file_entries
                            }

                            r = requests.post(
                                SETS_URL,
                                headers=headers,
                                json=payload
                            )
                            action = "Create"

                        results.append({
                            "Row": row_no + 1,
                            "Name": name,
                            "Action": action,
                            "Entries": len(payload["entries"]),
                            "Status": "Success" if r.status_code in (200, 201) else "Failed",
                            "JSON Sent": json.dumps(payload, indent=2)
                        })

                    except Exception as e:
                        results.append({
                            "Row": row_no + 1,
                            "Name": row.get("name"),
                            "Action": "Error",
                            "Entries": "",
                            "Status": str(e),
                            "JSON Sent": ""
                        })

            st.subheader("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE
    # ==================================================
    st.subheader("🗑️ Delete Paycode Event Sets")

    ids_input = st.text_input("Enter IDs (comma-separated)")
    if st.button("Delete"):
        for sid in [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]:
            r = requests.delete(f"{SETS_URL}/{sid}", headers=headers)
            if r.status_code in (200, 204):
                st.success(f"Deleted {sid}")
            else:
                st.error(f"Failed to delete {sid}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Paycode Event Sets")

    if st.button("Download Existing", use_container_width=True):
        r = requests.get(SETS_URL, headers=headers)
        if r.status_code != 200:
            st.error("Failed to fetch data")
            return

        rows = []
        for s in r.json():
            base = {"id": s["id"], "name": s["name"], "description": s["description"]}
            for i, e in enumerate(sorted(s.get("entries", []), key=lambda x: x["priority"]), start=1):
                base[f"PaycodeEvent{i}"] = e["paycodeEvent"]["id"]
                base[f"Priority{i}"] = e["priority"]
            rows.append(base)

        st.download_button(
            "⬇️ Download CSV",
            data=pd.DataFrame(rows).to_csv(index=False),
            file_name="paycode_event_sets_export.csv"
        )
