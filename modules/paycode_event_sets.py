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

    HOST = st.session_state.HOST.rstrip("/")
    SETS_URL = HOST + "/resource-server/api/paycode_event_sets"
    EVENTS_URL = HOST + "/resource-server/api/paycode_events"

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
            file_name="paycode_event_sets_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # UPLOAD PAYCODE EVENT SETS
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
        )
        df = df.fillna("")

        st.info(f"Rows detected: {len(df)}")

        if st.button("🚀 Process Upload", type="primary"):
            with st.spinner("⏳ Processing Paycode Event Sets..."):
                results = []

                for row_no, row in df.iterrows():
                    try:
                        name = str(row.get("name")).strip()
                        if not name:
                            raise ValueError("Name is mandatory")

                        payload = {
                            "name": name,
                            "description": str(row.get("description")).strip(),
                            "entries": []
                        }

                        # ---------- BUILD ENTRIES ----------
                        for i in range(1, 6):
                            event_raw = row.get(f"PaycodeEvent{i}")
                            priority_raw = row.get(f"Priority{i}")

                            if event_raw in ("", None):
                                continue

                            event_id = int(float(event_raw))
                            priority = (
                                int(priority_raw)
                                if str(priority_raw).isdigit()
                                else i
                            )

                            payload["entries"].append({
                                "paycodeEvent": {"id": event_id},
                                "priority": priority,
                                "overridable": False
                            })

                        if not payload["entries"]:
                            raise ValueError("At least one Paycode Event is required")

                        raw_id = str(row.get("id")).strip()

                        # ---------- CREATE / UPDATE ----------
                        if raw_id.isdigit():
                            set_id = int(raw_id)
                            payload["id"] = set_id
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
                            "Row": row_no + 1,
                            "Name": name,
                            "Action": action,
                            "Entries": len(payload["entries"]),
                            "HTTP Status": r.status_code,
                            "Status": "Success" if r.status_code in (200, 201) else "Failed",
                            "Message": r.text
                        })

                    except Exception as e:
                        results.append({
                            "Row": row_no + 1,
                            "Name": row.get("name"),
                            "Action": "Error",
                            "Entries": "",
                            "HTTP Status": "",
                            "Status": "Failed",
                            "Message": str(e)
                        })

            st.markdown("#### 📊 Upload Result")
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    st.divider()

    # ==================================================
    # DELETE PAYCODE EVENT SETS
    # ==================================================
    st.subheader("🗑️ Delete Paycode Event Sets")

    ids_input = st.text_input(
        "Enter Paycode Event Set IDs (comma-separated)",
        placeholder="Example: 82,83"
    )

    if st.button("Delete Paycode Event Sets", type="primary"):
        with st.spinner("⏳ Deleting Paycode Event Sets..."):
            ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]
            for sid in ids:
                r = requests.delete(f"{SETS_URL}/{sid}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted Paycode Event Set ID {sid}")
                else:
                    st.error(f"Failed to delete ID {sid} → {r.text}")

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING PAYCODE EVENT SETS
    # ==================================================
    st.subheader("⬇️ Download Existing Paycode Event Sets")

    if st.button("Download Existing Paycode Event Sets", use_container_width=True):
        with st.spinner("⏳ Fetching Paycode Event Sets..."):
            r = requests.get(SETS_URL, headers=headers)
            if r.status_code != 200:
                st.error("❌ Failed to fetch Paycode Event Sets")
                return

            rows = []
            for s in r.json():
                base = {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "description": s.get("description")
                }

                entries = sorted(
                    s.get("entries", []),
                    key=lambda x: x.get("priority", 0)
                )

                for idx, entry in enumerate(entries, start=1):
                    base[f"PaycodeEvent{idx}"] = entry.get("paycodeEvent", {}).get("id")
                    base[f"Priority{idx}"] = entry.get("priority")

                rows.append(base)

            sets_df = pd.DataFrame(rows)

            # ---------- SHEET 2 ----------
            r2 = requests.get(EVENTS_URL, headers=headers)
            events_df = (
                pd.DataFrame([
                    {
                        "id": e.get("id"),
                        "name": e.get("name"),
                        "description": e.get("description")
                    }
                    for e in r2.json()
                ]) if r2.status_code == 200 else
                pd.DataFrame(columns=["id", "name", "description"])
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                sets_df.to_excel(writer, index=False, sheet_name="Paycode_Event_Sets")
                events_df.to_excel(writer, index=False, sheet_name="Available_Paycode_Events")

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="paycode_event_sets_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
