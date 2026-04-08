import requests
import streamlit as st

SUPABASE_URL = "https://msyljqazsndtxpritfwy.supabase.co"
SUPABASE_KEY = "sb_publishable_HXoFqNveyeQcaFrL8suM1A_UBvL2rpZ"


def _supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _fetch_allowed_users():
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/allowed_users",
        headers=_supabase_headers(),
        params={"select": "id,username,created_at", "order": "created_at.desc"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _add_allowed_user(username: str):
    payload = {"username": username}
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/allowed_users",
        headers={**_supabase_headers(), "Prefer": "return=representation"},
        json=payload,
        timeout=10,
    )
    response.raise_for_status()


def _delete_allowed_user(user_id: str):
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/allowed_users",
        headers=_supabase_headers(),
        params={"id": f"eq.{user_id}"},
        timeout=10,
    )
    response.raise_for_status()


def access_control_ui():
    st.title("🔐 User Access Control")

    with st.container(border=True):
        st.subheader("Add User")
        new_username = st.text_input("username", key="access_control_username")
        if st.button("Add User", use_container_width=True):
            username = new_username.strip()
            if not username:
                st.error("Username is required.")
            else:
                try:
                    _add_allowed_user(username)
                    st.success(f"✅ Added user: {username}")
                    st.rerun()
                except requests.exceptions.RequestException as ex:
                    st.error(f"❌ Failed to add user: {ex}")

    with st.container(border=True):
        st.subheader("View Users")
        try:
            users = _fetch_allowed_users()
        except requests.exceptions.RequestException as ex:
            st.error(f"❌ Failed to fetch users: {ex}")
            return

        if not users:
            st.info("No users found.")
            return

        st.dataframe(
            [{"username": u.get("username"), "created_at": u.get("created_at")} for u in users],
            use_container_width=True,
        )

        st.subheader("Delete User")
        for user in users:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(user.get("username", "-"))
            with col2:
                if st.button("Delete", key=f"delete_user_{user['id']}"):
                    try:
                        _delete_allowed_user(user["id"])
                        st.success(f"✅ Deleted user: {user.get('username', '-')}")
                        st.rerun()
                    except requests.exceptions.RequestException as ex:
                        st.error(f"❌ Failed to delete user: {ex}")
