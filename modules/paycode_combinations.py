import streamlit as st
import pandas as pd
import requests
import io

from services.auth import require_token

# ======================================================
# MAIN UI
# ======================================================
def paycode_combinations_ui():
    st.header("🔗 Paycode Combinations")
    st.caption("Create, update and delete Paycode Combinations")

    # 🔐 SAFE TOKEN
    token = require_token()

    HOST = st.session_state.HOST.rstrip("/")
    COMBO_URL = f"{HOST}/resource-server/api/paycode_combinations"
    PAYCODES_URL = f"{HOST}/resource-server/api/paycodes"

    # ✅ CORRECT HEADERS (IMPORTANT)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    # ==================================================
    # DOWNLOAD TEMPLATE
    # ==================================================
    st.markdown("### 📥 Download Upload Template")

    template_df = pd.DataFrame(columns=[
        "id",
        "firstPaycode",
        "secondPaycode",
        "combinedPaycode",
        "inactive"
    ])

    if st.button("⬇️ Download Template", use_container_width=True):
        r = requests.get(PAYCODES_URL, headers=headers, timeout=10)

        paycodes_df = (
            pd.DataFrame(r.json())[["id", "code", "description"]]
            if r.status_code == 200
            else pd.DataFrame(columns=["id", "code", "description"])
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, sheet_name="Paycode_Combinations")
            paycodes_df.to_excel(writer, index=False, sheet_name="Available_Paycodes")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="paycode_combinations_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()

    # ==================================================
    # DELETE PAYCODE COMBINATIONS (FIXED)
    # ==================================================
    st.markdown("### 🗑️ Delete Paycode Combinations")

    ids_input = st.text_input(
        "Enter Combination IDs (comma-separated)",
        placeholder="924,925"
    )

    if st.button("Delete Combinations", type="primary"):
        ids = [i.strip() for i in ids_input.split(",") if i.strip().isdigit()]

        if not ids:
            st.warning("Please enter valid numeric IDs")
            return

        results = []

        with st.spinner("⏳ Deleting combinations..."):
            for cid in ids:
                try:
                    r = requests.delete(
                        f"{COMBO_URL}/{cid}",
                        headers=headers,
                        timeout=10   # 🔥 THIS FIXES FREEZE
                    )

                    if r.status_code in (200, 204):
                        results.append(f"✅ Deleted ID {cid}")
                    else:
                        results.append(f"❌ Failed ID {cid} → {r.status_code} | {r.text}")

                except requests.exceptions.Timeout:
                    results.append(f"⏱️ Timeout while deleting ID {cid}")

                except Exception as e:
                    results.append(f"❌ Error ID {cid} → {str(e)}")

        # 🔍 SHOW RESULTS
        st.markdown("#### 📄 Delete Results")
        for msg in results:
            if msg.startswith("✅"):
                st.success(msg)
            elif msg.startswith("⏱️"):
                st.warning(msg)
            else:
                st.error(msg)

    st.divider()

    # ==================================================
    # DOWNLOAD EXISTING COMBINATIONS
    # ==================================================
    st.markdown("### ⬇️ Download Existing Paycode Combinations")

    if st.button("Download Existing Combinations", use_container_width=True):
        r = requests.get(COMBO_URL, headers=headers, timeout=10)

        if r.status_code != 200:
            st.error("❌ Failed to fetch combinations")
            return

        rows = [{
            "id": c.get("id"),
            "firstPaycode": c.get("firstPaycode", {}).get("id"),
            "secondPaycode": c.get("secondPaycode", {}).get("id"),
            "combinedPaycode": c.get("combinedPaycode", {}).get("id"),
            "inactive": c.get("inactive", False)
        } for c in r.json()]

        df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name="paycode_combinations_export.csv",
            mime="text/csv"
        )
