import streamlit as st
import pandas as pd
import requests
import io

# ======================================================
# PAYCODE EVENT SETS UI
# ======================================================
def paycode_event_sets_ui():
    st.header("🧩 Paycode Event Sets")
    st.caption("Create, update, delete and download Paycode Event Sets")

    # --------------------------------------------------
    # PRECHECK
    # --------------------------------------------------
    if "token" not in st.session_state or not st.session_state.token:
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")
    SETS_URL = f"{HOST}/resource-server/api/paycode_event_sets"
    EVENTS_URL = f"{HOST}/resource-server/api/paycode_events"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    st.subheader("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
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
                {
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "description": e.get("description")
                }
                for e in r.json()
            ])
            if r.status_code == 200
            else pd.DataFrame(columns=["id", "name", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode_Event_Sets")
            events_df.to_excel(writer, index=False, sheet_name="Available_Paycode_Events")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_event_sets_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    st.subheader("📤 Upload Paycode Event Sets")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        ["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        df = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        ).fillna("")

        st.success(f"Rows detected: {len(df)}")
        st.dataframe(df, use_container_width=True)

        if st.button("🚀 Process Upload", type="primary", use_container_width=True):
            results = []

            with st.spinner("⏳ Processing Paycode Event Sets..."):
                for idx, row in df.iterrows():
                    try:
                        name = str(row.get("name", "")).strip()
                        if not name:
                            raise ValueError("Name is mandatory")

                        raw_id = str(row.get("id", "")).strip()
                        is_update = raw_id.isdigit()

                        # ----------------------------------------------
                        # FETCH EXISTING SET (ONLY FOR UPDATE)
                        # ----------------------------------------------
                        existing_entry_map = {}

                        if is_update:
                            set_id = int(raw_id)
                            get_r = requests.get(f"{SETS_URL}/{set_id}", headers=headers)

                            if get_r.status_code != 200:
                                raise ValueError(f"Unable to fetch existing set ID {set_id}")

                            existing_data = get_r.json()
                            for e in existing_data.get("entries", []):
                                pe_id = e.get("paycodeEvent", {}).get("id")
                                if pe_id:
                                    existing_entry_map[pe_id] = e.get("id")

                        # ----------------------------------------------
                        # BUILD PAYLOAD
                        # ----------------------------------------------
                        payload = {
                            "name": name,
                            "description": str(row.get("description", "")).strip() or name,
                            "entries": []
                        }

                        for i in range(1, 6):
                            event_val = row.get(f"PaycodeEvent{i}", "")
                            priority_val = row.get(f"Priority{i}", "")

                            if str(event_val).strip() == "":
                                continue

                            event_id = int(float(event_val))
                            priority = int(float(priority_val)) if str(priority_val).strip() else i

                            entry = {
                                "paycodeEvent": {"id": event_id},
                                "priority": priority,
                                "overridable": False
                            }

                            # ✅ REQUIRED FOR UPDATE
                            if event_id in existing_entry_map:
                                entry["id"] = existing_entry_map[event_id]

                            payload["entries"].append(entry)

                        if not payload["entries"]:
                            raise ValueError("At least one Paycode Event is required")

                        # ----------------------------------------------
                        # CREATE / UPDATE
                        # ----------------------------------------------
                        if is_update:
                            r = requests.put(
                                f"{SETS_URL}/{set_id}",
                                headers=headers,
                                json=payload
                            )
                            action = "Update"
                        else:
                            r = requests.post(
                                SETS_URL,
                                headers=headers,
                                json=payload
                            )
                            action = "Create"

                        results.append({
                            "Row": idx + 1,
                            "Name": name,
                            "Action": action,
                            "Entries": len(payload["entries"]),
                            "Status": "Success" if r.status_code in (200, 201) else "Failed"
                        })

                    except Exception as e:
                        results.append({
                            "Row": idx + 1,
                            "Name": row.get("name", ""),
                            "Action": "Error",
                            "Entries": "",
                            "Status": str(e)
                        })

            st.subheader("📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # 3️⃣ DELETE
    # ==================================================
    st.subheader("🗑️ Delete Paycode Event Sets")

    ids_input = st.text_input(
        "Enter Paycode Event Set IDs (comma-separated)",
        placeholder="Example: 392,390"
    )

    if st.button("Delete Paycode Event Sets", use_container_width=True):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
        with st.spinner("⏳ Deleting..."):
            for sid in ids:
                r = requests.delete(f"{SETS_URL}/{sid}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted ID {sid}")
                else:
                    st.error(f"Failed to delete {sid}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Paycode Event Sets")

    if st.button("Download Existing Paycode Event Sets", use_container_width=True):
        with st.spinner("⏳ Fetching data..."):
            r = requests.get(SETS_URL, headers=headers)
            if r.status_code != 200:
                st.error("Failed to fetch Paycode Event Sets")
                return

            rows = []
            for s in r.json():
                base = {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "description": s.get("description")
                }

                for i, entry in enumerate(
                    sorted(s.get("entries", []), key=lambda x: x.get("priority", 0)),
                    start=1
                ):
                    base[f"PaycodeEvent{i}"] = entry.get("paycodeEvent", {}).get("id")
                    base[f"Priority{i}"] = entry.get("priority")

                rows.append(base)

            sets_df = pd.DataFrame(rows)

            r2 = requests.get(EVENTS_URL, headers=headers)
            events_df = (
                pd.DataFrame([
                    {
                        "id": e.get("id"),
                        "name": e.get("name"),
                        "description": e.get("description")
                    }
                    for e in r2.json()
                ])
                if r2.status_code == 200
                else pd.DataFrame(columns=["id", "name", "description"])
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                sets_df.to_excel(writer, index=False, sheet_name="Paycode_Event_Sets")
                events_df.to_excel(writer, index=False, sheet_name="Available_Paycode_Events")

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="paycode_event_sets_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
