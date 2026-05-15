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

    # --------------------------------------------------
    # TEMPLATE FORMAT
    # --------------------------------------------------
    template_df = pd.DataFrame(columns=[
        "id",
        "name",
        "description",
        "PaycodeEvent",
        "Priority"
    ])

    # --------------------------------------------------
    # PAYCODE EVENTS EXPORT
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

        events_df = pd.DataFrame(columns=[
            "id",
            "name",
            "description"
        ])

    # --------------------------------------------------
    # EXCEL OUTPUT
    # --------------------------------------------------
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # Upload Template
        template_df.to_excel(
            writer,
            index=False,
            sheet_name="Upload_Template"
        )

        # Paycode Event Export
        events_df.to_excel(
            writer,
            index=False,
            sheet_name="Paycode_Events"
        )

    st.download_button(
        "⬇️ Download Template",
        data=output.getvalue(),
        file_name="paycode_event_sets_template.xlsx",
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # 2️⃣ UPLOAD
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
        # PROCESS
        # ==================================================
        if st.button(
            "🚀 Process Upload",
            type="primary",
            use_container_width=True
        ):

            results = []

            # --------------------------------------------------
            # HELPERS
            # --------------------------------------------------
            def parse_int(x):
                try:
                    return int(float(x))
                except:
                    return None

            # --------------------------------------------------
            # NORMALIZE
            # --------------------------------------------------
            df["id"] = df["id"].apply(parse_int)

            # --------------------------------------------------
            # UPDATE GROUPS
            # --------------------------------------------------
            update_groups = df[
                df["id"].notna()
            ].groupby("id")

            # --------------------------------------------------
            # CREATE GROUPS
            # --------------------------------------------------
            create_groups = df[
                df["id"].isna()
            ].groupby("name")

            with st.spinner("⏳ Processing..."):

                # ==================================================
                # UPDATE EXISTING
                # ==================================================
                for set_id, group in update_groups:

                    try:

                        first = group.iloc[0]

                        payload = {
                            "id": int(set_id),
                            "name": str(first["name"]).strip(),
                            "description": (
                                str(first["description"]).strip()
                                or str(first["name"]).strip()
                            ),
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():

                            paycode_event_id = parse_int(
                                row.get("PaycodeEvent")
                            )

                            if not paycode_event_id:
                                continue

                            if paycode_event_id in seen:
                                continue

                            seen.add(paycode_event_id)

                            payload["entries"].append({
                                "paycodeEvent": {
                                    "id": paycode_event_id
                                },
                                "priority": (
                                    parse_int(row.get("Priority")) or 1
                                ),
                                "overridable": False
                            })

                        r = requests.put(
                            f"{SETS_URL}/{int(set_id)}",
                            headers=headers,
                            json=payload
                        )

                        results.append({
                            "id": set_id,
                            "name": payload["name"],
                            "action": "UPDATE",
                            "entries": len(payload["entries"]),
                            "status": (
                                "Success"
                                if r.status_code in (200, 201)
                                else f"Failed ({r.status_code})"
                            )
                        })

                    except Exception as e:

                        results.append({
                            "id": set_id,
                            "name": "",
                            "action": "UPDATE",
                            "entries": "",
                            "status": str(e)
                        })

                # ==================================================
                # CREATE NEW
                # ==================================================
                for name, group in create_groups:

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

                            paycode_event_id = parse_int(
                                row.get("PaycodeEvent")
                            )

                            if not paycode_event_id:
                                continue

                            if paycode_event_id in seen:
                                continue

                            seen.add(paycode_event_id)

                            payload["entries"].append({
                                "paycodeEvent": {
                                    "id": paycode_event_id
                                },
                                "priority": (
                                    parse_int(row.get("Priority")) or 1
                                ),
                                "overridable": False
                            })

                        r = requests.post(
                            SETS_URL,
                            headers=headers,
                            json=payload
                        )

                        results.append({
                            "id": "",
                            "name": payload["name"],
                            "action": "CREATE",
                            "entries": len(payload["entries"]),
                            "status": (
                                "Success"
                                if r.status_code in (200, 201)
                                else f"Failed ({r.status_code})"
                            )
                        })

                    except Exception as e:

                        results.append({
                            "id": "",
                            "name": name,
                            "action": "CREATE",
                            "entries": "",
                            "status": str(e)
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
        placeholder="143,144"
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
    # 4️⃣ EXPORT EXISTING
    # ==================================================
    section_header("⬇️ Download Existing Paycode Event Sets")

    with st.spinner("⏳ Fetching..."):

        r = requests.get(
            FULL_SETS_URL,
            headers=headers
        )

        if r.status_code != 200:
            st.error("Failed to fetch data")
            return

        rows = []

        for item in r.json():

            entries = item.get("entries", [])

            for entry in entries:

                rows.append({

                    "id": item.get("id"),

                    "name": item.get("name"),

                    "description": item.get("description"),

                    "PaycodeEvent": (
                        entry.get("paycodeEvent", {}).get("id")
                    ),

                    "Priority": (
                        entry.get("priority")
                    )

                })

        export_df = pd.DataFrame(rows)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            export_df.to_excel(
                writer,
                index=False,
                sheet_name="Paycode_Event_Sets"
            )

    st.download_button(
        "⬇️ Download Existing Paycode Event Sets",
        data=output.getvalue(),
        file_name="paycode_event_sets_export.xlsx",
        use_container_width=True
    )
