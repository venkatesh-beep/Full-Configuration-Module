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
    if not st.session_state.get("token"):
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
        "id", "name", "description",
        "PaycodeEvent1", "Priority1",
        "PaycodeEvent2", "Priority2",
        "PaycodeEvent3", "Priority3",
        "PaycodeEvent4", "Priority4",
        "PaycodeEvent5", "Priority5"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):

        # ---- Sheet 2: Paycode Events
        r1 = requests.get(EVENTS_URL, headers=headers)
        events_df = (
            pd.DataFrame([
                {
                    "id": e["id"],
                    "name": e["name"],
                    "description": e["description"]
                } for e in r1.json()
            ]) if r1.status_code == 200 else pd.DataFrame(
                columns=["id", "name", "description"]
            )
        )

        # ---- Sheet 3: Paycode Event Sets (NEW)
        r2 = requests.get(SETS_URL, headers=headers)
        sets_df = (
            pd.DataFrame([
                {
                    "id": s["id"],
                    "name": s["name"],
                    "description": s["description"]
                } for s in r2.json()
            ]) if r2.status_code == 200 else pd.DataFrame(
                columns=["id", "name", "description"]
            )
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode_Event_Sets")
            events_df.to_excel(writer, index=False, sheet_name="Available_Paycode_Events")
            sets_df.to_excel(writer, index=False, sheet_name="Available_Paycode_Sets")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_event_sets_template.xlsx",
            use_container_width=True
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

        st.success(f"Rows detected: {len(df)}")
        st.dataframe(df, use_container_width=True)

        if st.button("🚀 Process Upload", type="primary", use_container_width=True):

            results = []

            # -------------------------------
            # NORMALIZE
            # -------------------------------
            def parse_id(x):
                try:
                    return int(float(x))
                except:
                    return None

            df["id"] = df["id"].apply(parse_id)
            df["name"] = df["name"].astype(str).str.strip()

            id_groups = df[df["id"].notna()].groupby("id")
            name_groups = df[df["id"].isna()].groupby("name")

            with st.spinner("⏳ Processing Paycode Event Sets..."):

                # ==================================================
                # UPDATE (PUT) — GROUP BY ID
                # ==================================================
                for set_id, group in id_groups:
                    try:
                        set_id = int(set_id)
                        name = group.iloc[0]["name"]
                        description = str(group.iloc[0].get("description", "")).strip() or name

                        payload = {
                            "id": set_id,
                            "name": name,
                            "description": description,
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():
                            for i in range(1, 6):
                                ev = row.get(f"PaycodeEvent{i}", "")
                                pr = row.get(f"Priority{i}", "")

                                if str(ev).strip() == "":
                                    continue

                                ev_id = int(float(ev))
                                if ev_id in seen:
                                    continue
                                seen.add(ev_id)

                                payload["entries"].append({
                                    "paycodeEvent": {"id": ev_id},
                                    "priority": int(float(pr)) if str(pr).strip() else 1,
                                    "overridable": False
                                })

                        if not payload["entries"]:
                            raise Exception("No Paycode Events found")

                        r = requests.put(
                            f"{SETS_URL}/{set_id}",
                            headers=headers,
                            json=payload
                        )

                        results.append({
                            "Key": f"ID {set_id}",
                            "Name": name,
                            "Action": "UPDATE",
                            "Entries": len(payload["entries"]),
                            "Status": "Success" if r.status_code in (200, 201)
                                      else f"Failed ({r.status_code})"
                        })

                    except Exception as e:
                        results.append({
                            "Key": f"ID {set_id}",
                            "Name": "",
                            "Action": "UPDATE",
                            "Entries": "",
                            "Status": str(e)
                        })

                # ==================================================
                # CREATE (POST) — GROUP BY NAME
                # ==================================================
                for name, group in name_groups:
                    if not name:
                        continue

                    try:
                        description = str(group.iloc[0].get("description", "")).strip() or name

                        payload = {
                            "name": name,
                            "description": description,
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():
                            for i in range(1, 6):
                                ev = row.get(f"PaycodeEvent{i}", "")
                                pr = row.get(f"Priority{i}", "")

                                if str(ev).strip() == "":
                                    continue

                                ev_id = int(float(ev))
                                if ev_id in seen:
                                    continue
                                seen.add(ev_id)

                                payload["entries"].append({
                                    "paycodeEvent": {"id": ev_id},
                                    "priority": int(float(pr)) if str(pr).strip() else 1,
                                    "overridable": False
                                })

                        if not payload["entries"]:
                            raise Exception("No Paycode Events found")

                        r = requests.post(
                            SETS_URL,
                            headers=headers,
                            json=payload
                        )

                        results.append({
                            "Key": name,
                            "Name": name,
                            "Action": "CREATE",
                            "Entries": len(payload["entries"]),
                            "Status": "Success" if r.status_code in (200, 201)
                                      else f"Failed ({r.status_code})"
                        })

                    except Exception as e:
                        results.append({
                            "Key": name,
                            "Name": name,
                            "Action": "CREATE",
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

    ids_input = st.text_input("Enter IDs (comma-separated)", placeholder="392,390")

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
        with st.spinner("⏳ Fetching..."):
            r = requests.get(SETS_URL, headers=headers)
            if r.status_code != 200:
                st.error("Failed to fetch data")
                return

            rows = []
            for s in r.json():
                base = {
                    "id": s["id"],
                    "name": s["name"],
                    "description": s["description"]
                }

                for i, e in enumerate(
                    sorted(s.get("entries", []), key=lambda x: x["priority"]), start=1
                ):
                    base[f"PaycodeEvent{i}"] = e["paycodeEvent"]["id"]
                    base[f"Priority{i}"] = e["priority"]

                rows.append(base)

            output = io.BytesIO()
            pd.DataFrame(rows).to_excel(output, index=False)

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name="paycode_event_sets_export.xlsx",
                use_container_width=True
            )
