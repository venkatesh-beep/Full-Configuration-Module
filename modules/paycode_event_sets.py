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
    SETS_URL = f"{HOST}/resource-server/api/paycode_event_sets"
    EVENTS_URL = f"{HOST}/resource-server/api/paycode_events"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
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
    # 2️⃣ UPLOAD & PROCESS
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
                        name = str(row.get("name", "")).strip()
                        if not name:
                            raise ValueError("Name is mandatory")

                        raw_id = str(row.get("id", "")).strip()
                        description = str(row.get("description", "")).strip() or name

                        payload = {
                            "name": name,
                            "description": description
                        }

                        # ---------------- ENTRIES (OPTIONAL) ----------------
                        entries = []

                        for i in range(1, 6):
                            ev = row.get(f"PaycodeEvent{i}")
                            pr = row.get(f"Priority{i}")

                            if ev in ("", None):
                                continue

                            entries.append({
                                "paycodeEvent": {"id": int(float(ev))},
                                "priority": int(pr) if str(pr).isdigit() else i,
                                "overridable": False
                            })

                        # ---------------- UPDATE ----------------
                        if raw_id.isdigit():
                            set_id = int(raw_id)
                            payload["id"] = set_id

                            # ✅ Only send entries if provided
                            if entries:
                                payload["entries"] = entries

                            r = requests.put(
                                f"{SETS_URL}/{set_id}",
                                headers=headers,
                                json=payload
                            )
                            action = "Update"

                        # ---------------- CREATE ----------------
                        else:
                            if not entries:
                                raise ValueError("Entries are mandatory for Create")

                            payload["entries"] = entries

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
                            "Entries": len(entries),
                            "Status": "Success" if r.status_code in (200, 201) else "Failed"
                        })

                    except Exception as e:
                        results.append({
                            "Row": row_no + 1,
                            "Name": row.get("name"),
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
        placeholder="Example: 82,83"
    )

    if st.button("Delete Paycode Event Sets"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]

        with st.spinner("⏳ Deleting..."):
            for sid in ids:
                r = requests.delete(f"{SETS_URL}/{sid}", headers=headers)
                if r.status_code in (200, 204):
                    st.success(f"Deleted ID {sid}")
                else:
                    st.error(f"Failed to delete ID {sid}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING
    # ==================================================
    st.subheader("⬇️ Download Existing Paycode Event Sets")

    if st.button("Download Existing Paycode Event Sets", use_container_width=True):
        with st.spinner("⏳ Fetching data..."):
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

                for idx, entry in enumerate(
                    sorted(s.get("entries", []), key=lambda x: x.get("priority", 0)),
                    start=1
                ):
                    base[f"PaycodeEvent{idx}"] = entry.get("paycodeEvent", {}).get("id")
                    base[f"Priority{idx}"] = entry.get("priority")

                rows.append(base)

            df_out = pd.DataFrame(rows)

            st.download_button(
                "⬇️ Download CSV",
                data=df_out.to_csv(index=False),
                file_name="paycode_event_sets_export.csv",
                mime="text/csv"
            )
