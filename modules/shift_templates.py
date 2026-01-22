import streamlit as st
import requests
import json

BASE_URL = "https://saas-beeforce.labour.tech"
SHIFT_API = f"{BASE_URL}/resource-server/api/shift_templates/"

def shift_templates_ui():
    st.header("🕒 Shift Templates")

    # ==============================
    # AUTH TOKEN
    # ==============================
    token = st.session_state.get("access_token")

    if not token:
        st.warning("Please login to access Shift Templates")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # ==============================
    # SAMPLE TEMPLATE DOWNLOAD
    # ==============================
    st.subheader("📥 Download Sample Shift Template")

    sample_template = {
        "name": "Ameenpur - A Shift",
        "description": "Ameenpur - A Shift",
        "startTime": "1970-01-01 06:00:00",
        "endTime": "1970-01-01 14:00:00",
        "beforeStartToleranceMinute": 239,
        "afterStartToleranceMinute": 120,
        "lateInToleranceMinute": 10,
        "earlyOutToleranceMinute": 10,
        "paycodes": [
            {"startMinute": 0, "endMinute": 240, "paycode": {"id": 257}, "max": False},
            {"startMinute": 241, "endMinute": 360, "paycode": {"id": 258}, "max": False},
            {"startMinute": 361, "paycode": {"id": 256}, "max": True}
        ],
        "report": False,
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
        "saturday": True,
        "sunday": True
    }

    st.download_button(
        label="⬇️ Download Sample JSON",
        data=json.dumps(sample_template, indent=2),
        file_name="shift_template_sample.json",
        mime="application/json"
    )

    st.divider()

    # ==============================
    # GET & DOWNLOAD EXISTING SHIFTS
    # ==============================
    st.subheader("📤 Download Existing Shift Templates")

    if st.button("Fetch Shift Templates"):
        try:
            resp = requests.get(SHIFT_API, headers=headers)
            if resp.status_code == 200:
                shifts = resp.json()

                st.success(f"Fetched {len(shifts)} shift templates")

                st.download_button(
                    label="⬇️ Download All Shifts (JSON)",
                    data=json.dumps(shifts, indent=2),
                    file_name="shift_templates_existing.json",
                    mime="application/json"
                )

                with st.expander("👀 Preview Shift Templates"):
                    st.json(shifts)

            else:
                st.error(f"Failed to fetch shifts: {resp.status_code}")
        except Exception as e:
            st.error(str(e))

    st.divider()

    # ==============================
    # DELETE SHIFT TEMPLATE
    # ==============================
    st.subheader("🗑️ Delete Shift Template")

    shift_id = st.text_input("Enter Shift Template ID to Delete")

    if st.button("Delete Shift Template"):
        if not shift_id.strip():
            st.warning("Please enter a Shift Template ID")
            return

        try:
            delete_url = f"{SHIFT_API}{shift_id}"
            resp = requests.delete(delete_url, headers=headers)

            if resp.status_code in (200, 204):
                st.success(f"Shift Template ID {shift_id} deleted successfully")
            else:
                st.error(f"Delete failed: {resp.status_code} - {resp.text}")

        except Exception as e:
            st.error(str(e))
