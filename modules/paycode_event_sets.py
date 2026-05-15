import streamlit as st
import pandas as pd
import requests
import io

from modules.ui_helpers import module_header, section_header

# ======================================================
# PAYCODE EVENT SETS UI
# ======================================================
def paycode_event_sets_ui():

    module_header(
        "🧩 Paycode Event Sets",
        "Create, update, delete and download Paycode Event Sets"
    )

    # ==================================================
    # PRECHECK
    # ==================================================
    if not st.session_state.get("token"):
        st.error("Please login first")
        return

    HOST = st.session_state.HOST.rstrip("/")

    SETS_URL = f"{HOST}/resource-server/api/paycode_event_sets"
    FULL_SETS_URL = f"{HOST}/resource-server/api/paycode_event_sets/?projection=FULL"
    EVENTS_URL = f"{HOST}/resource-server/api/paycode_events"

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ==================================================
    # 1️⃣ DOWNLOAD TEMPLATE
    # ==================================================
    section_header("📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "PaycodeEvent",
        "Priority"
    ])

    # --------------------------------------------------
    # Available Paycode Events
    # --------------------------------------------------
    r1 = requests.get(EVENTS_URL, headers=headers)

    if r1.status_code == 200:
        events_df = pd.DataFrame([
            {
                "id": e.get("id"),
                "name": e.get("name"),
                "description": e.get("description")
            }
            for e in r1.json()
        ])
    else:
        events_df = pd.DataFrame(
            columns=["id", "name", "description"]
        )

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        template_df.to_excel(
            writer,
            index=False,
            sheet_name="Paycode_Event_Sets"
        )

        events_df.to_excel(
            writer,
            index=False,
            sheet_name="Available_Paycode_Events"
        )

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="paycode_event_sets_template.xlsx",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD & PROCESS
    # ==================================================
    section_header("📤 Upload Paycode Event Sets")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        ["csv", "xlsx", "xls"]
    )

    if uploaded_file:

        # --------------------------------------------------
        # READ FILE
        # --------------------------------------------------
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df = df.fillna("")

        st.success(f"Rows detected: {len(df)}")
        st.dataframe(df, use_container_width=True)

        # ==================================================
        # PROCESS BUTTON
        # ==================================================
        if st.button(
            "🚀 Process Upload",
            type="primary",
            use_container_width=True
        ):

            results = []

            # --------------------------------------------------
            # NORMALIZE
            # --------------------------------------------------
            def parse_id(x):
                try:
                    return int(float(x))
                except:
                    return None

            df["id"] = df["id"].apply(parse_id)
            df["name"] = df["name"].astype(str).str.strip()

            # --------------------------------------------------
            # GROUPS
            # --------------------------------------------------
            id_groups = df[df["id"].notna()].groupby("id")
            name_groups = df[df["id"].isna()].groupby("name")

            with st.spinner("⏳ Processing..."):

                # ==================================================
                # UPDATE EXISTING (PUT)
                # ==================================================
                for set_id, group in id_groups:

                    try:

                        set_id = int(set_id)

                        first = group.iloc[0]

                        payload = {
                            "id": set_id,
                            "name": str(first["name"]).strip(),
                            "description": (
                                str(first["description"]).strip()
                                or str(first["name"]).strip()
                            ),
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():

                            ev = row.get("PaycodeEvent", "")
                            pr = row.get("Priority", "")

                            if str(ev).strip() == "":
                                continue

                            ev_id = int(float(ev))

                            if ev_id in seen:
                                continue

                            seen.add(ev_id)

                            payload["entries"].append({
                                "paycodeEvent": {
                                    "id": ev_id
                                },
                                "priority": (
                                    int(float(pr))
                                    if str(pr).strip()
                                    else 1
                                ),
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
                            "Key": set_id,
                            "Name": payload["name"],
                            "Action": "UPDATE",
                            "Entries": len(payload["entries"]),
                            "Status": (
                                "Success"
                                if r.status_code in (200, 201)
                                else f"Failed ({r.status_code})"
                            )
                        })

                    except Exception as e:

                        results.append({
                            "Key": set_id,
                            "Name": "",
                            "Action": "UPDATE",
                            "Entries": "",
                            "Status": str(e)
                        })

                # ==================================================
                # CREATE NEW (POST)
                # ==================================================
                for name, group in name_groups:

                    if not str(name).strip():
                        continue

                    try:

                        first = group.iloc[0]

                        payload = {
                            "name": str(name).strip(),
                            "description": (
                                str(first["description"]).strip()
                                or str(name).strip()
                            ),
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():

                            ev = row.get("PaycodeEvent", "")
                            pr = row.get("Priority", "")

                            if str(ev).strip() == "":
                                continue

                            ev_id = int(float(ev))

                            if ev_id in seen:
                                continue

                            seen.add(ev_id)

                            payload["entries"].append({
                                "paycodeEvent": {
                                    "id": ev_id
                                },
                                "priority": (
                                    int(float(pr))
                                    if str(pr).strip()
                                    else 1
                                ),
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
                            "Status": (
                                "Success"
                                if r.status_code in (200, 201)
                                else f"Failed ({r.status_code})"
                            )
                        })

                    except Exception as e:

                        results.append({
                            "Key": name,
                            "Name": "",
                            "Action": "CREATE",
                            "Entries": "",
                            "Status": str(e)
                        })

            # ==================================================
            # RESULT
            # ==================================================
            section_header("📊 Upload Result")

            st.dataframe(
                pd.DataFrame(results),
                use_container_width=True
            )

    st.divider()

    # ==================================================
    # 3️⃣ DELETE
    # ==================================================
    section_header("🗑️ Delete Paycode Event Sets")

    ids_input = st.text_input(
        "Enter IDs (comma-separated)",
        placeholder="392,390"
    )

    if st.button(
        "Delete Paycode Event Sets",
        use_container_width=True
    ):

        ids = [
            i.strip()
            for i in ids_input.split(",")
            if i.strip().isdigit()
        ]

        with st.spinner("⏳ Deleting..."):

            for sid in ids:

                r = requests.delete(
                    f"{SETS_URL}/{sid}",
                    headers=headers
                )

                if r.status_code in (200, 204):
                    st.success(f"Deleted ID {sid}")
                else:
                    st.error(f"Failed to delete ID {sid}")

    st.divider()

    # ==================================================
    # 4️⃣ DOWNLOAD EXISTING
    # ==================================================
    section_header("⬇️ Download Existing Paycode Event Sets")

    with st.spinner("⏳ Fetching..."):

        r = requests.get(FULL_SETS_URL, headers=headers)

        if r.status_code != 200:
            st.error("Failed to fetch data")
            return

        rows = []

        for item in r.json():

            row = {
                "id": item.get("id"),
                "name": item.get("name"),
                "description": item.get("description")
            }

            entries = item.get("entries", [])

            for index, entry in enumerate(entries, start=1):

                row[f"PaycodeEvent{index}"] = (
                    entry.get("paycodeEvent", {}).get("name", "")
                )

                row[f"Priority{index}"] = (
                    entry.get("priority", "")
                )

            rows.append(row)

        export_df = pd.DataFrame(rows)

        output = io.BytesIO()

        export_df.to_excel(
            output,
            index=False,
            engine="openpyxl"
        )

    st.download_button(
        "⬇️ Download Existing Paycode Event Sets",
        data=output.getvalue(),
        file_name="paycode_event_sets_export.xlsx",
        use_container_width=True
    )
