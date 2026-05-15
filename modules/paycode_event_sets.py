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
        "set_id",
        "set_name",
        "set_description",
        "entry_id",
        "priority",
        "paycode_event_id",
        "paycode_event_name"
    ])

    # --------------------------------------------------
    # AVAILABLE PAYCODE EVENTS
    # --------------------------------------------------
    r1 = requests.get(EVENTS_URL, headers=headers)

    if r1.status_code == 200:

        events_df = pd.DataFrame([
            {
                "paycode_event_id": e.get("id"),
                "paycode_event_name": e.get("name"),
                "description": e.get("description")
            }
            for e in r1.json()
        ])

    else:

        events_df = pd.DataFrame(columns=[
            "paycode_event_id",
            "paycode_event_name",
            "description"
        ])

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
            # NORMALIZE
            # --------------------------------------------------
            def parse_int(x):
                try:
                    return int(float(x))
                except:
                    return None

            df["set_id"] = df["set_id"].apply(parse_int)

            # --------------------------------------------------
            # UPDATE GROUPS
            # --------------------------------------------------
            update_groups = df[
                df["set_id"].notna()
            ].groupby("set_id")

            # --------------------------------------------------
            # CREATE GROUPS
            # --------------------------------------------------
            create_groups = df[
                df["set_id"].isna()
            ].groupby("set_name")

            with st.spinner("⏳ Processing..."):

                # ==================================================
                # UPDATE EXISTING
                # ==================================================
                for set_id, group in update_groups:

                    try:

                        first = group.iloc[0]

                        payload = {
                            "id": int(set_id),
                            "name": str(first["set_name"]).strip(),
                            "description": (
                                str(first["set_description"]).strip()
                                or str(first["set_name"]).strip()
                            ),
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():

                            paycode_event_id = parse_int(
                                row.get("paycode_event_id")
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
                                    parse_int(row.get("priority")) or 1
                                ),
                                "overridable": False
                            })

                        r = requests.put(
                            f"{SETS_URL}/{int(set_id)}",
                            headers=headers,
                            json=payload
                        )

                        results.append({
                            "set_id": set_id,
                            "set_name": payload["name"],
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
                            "set_id": set_id,
                            "set_name": "",
                            "action": "UPDATE",
                            "entries": "",
                            "status": str(e)
                        })

                # ==================================================
                # CREATE NEW
                # ==================================================
                for set_name, group in create_groups:

                    try:

                        first = group.iloc[0]

                        payload = {
                            "name": str(set_name).strip(),
                            "description": (
                                str(first["set_description"]).strip()
                                or str(set_name).strip()
                            ),
                            "entries": []
                        }

                        seen = set()

                        for _, row in group.iterrows():

                            paycode_event_id = parse_int(
                                row.get("paycode_event_id")
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
                                    parse_int(row.get("priority")) or 1
                                ),
                                "overridable": False
                            })

                        r = requests.post(
                            SETS_URL,
                            headers=headers,
                            json=payload
                        )

                        results.append({
                            "set_id": "",
                            "set_name": payload["name"],
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
                            "set_id": "",
                            "set_name": set_name,
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

                    "set_id": item.get("id"),

                    "set_name": item.get("name"),

                    "set_description": item.get("description"),

                    "entry_id": entry.get("id"),

                    "priority": entry.get("priority"),

                    "paycode_event_id": (
                        entry.get("paycodeEvent", {}).get("id")
                    ),

                    "paycode_event_name": (
                        entry.get("paycodeEvent", {}).get("name")
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
