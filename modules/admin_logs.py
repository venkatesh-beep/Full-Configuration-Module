import io
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st

SUPABASE_URL = "https://msyljqazsndtxpritfwy.supabase.co"
SUPABASE_KEY = "sb_publishable_HXoFqNveyeQcaFrL8suM1A_UBvL2rpZ"


def _supabase_headers(count=False):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    if count:
        headers["Prefer"] = "count=exact"
    return headers


def _build_filters(params, username, module, action, search, start_date, end_date):
    if username:
        params["username"] = f"eq.{username}"
    if module:
        params["module"] = f"eq.{module}"
    if action:
        params["action"] = f"ilike.*{action}*"
    if start_date and end_date:
        start_iso = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        end_iso = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc).isoformat()
        params["and"] = f"(created_at.gte.{start_iso},created_at.lte.{end_iso})"
    elif start_date:
        start_iso = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        params["created_at"] = f"gte.{start_iso}"
    elif end_date:
        end_iso = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc).isoformat()
        params["created_at"] = f"lte.{end_iso}"
    if search:
        safe = search.replace(",", "")
        params["or"] = f"(username.ilike.*{safe}*,module.ilike.*{safe}*,action.ilike.*{safe}*)"


def _fetch_logs(page, page_size, username, module, action, search, start_date, end_date):
    params = {
        "select": "id,username,module,action,file_name,file_url,created_at",
        "order": "created_at.desc",
    }
    _build_filters(params, username, module, action, search, start_date, end_date)

    start = (page - 1) * page_size
    end = start + page_size - 1

    headers = _supabase_headers(count=True)
    headers["Range"] = f"{start}-{end}"

    response = requests.get(f"{SUPABASE_URL}/rest/v1/logs", headers=headers, params=params, timeout=20)
    response.raise_for_status()

    total_count = int(response.headers.get("content-range", "0-0/0").split("/")[-1])
    rows = response.json()
    return rows, total_count


def _fetch_filter_options():
    params = {"select": "username,module", "order": "created_at.desc", "limit": 1000}
    response = requests.get(f"{SUPABASE_URL}/rest/v1/logs", headers=_supabase_headers(), params=params, timeout=20)
    response.raise_for_status()
    rows = response.json()
    usernames = sorted({r.get("username") for r in rows if r.get("username")})
    modules = sorted({r.get("module") for r in rows if r.get("module")})
    return usernames, modules


def _make_downloadable_url(file_url: str | None):
    if not file_url:
        return None

    if "object/sign/" in file_url or "token=" in file_url:
        return file_url

    marker_public = f"/storage/v1/object/public/logs-files/"
    marker_object = f"/storage/v1/object/logs-files/"
    path = None

    if marker_public in file_url:
        path = file_url.split(marker_public, 1)[1]
    elif marker_object in file_url:
        path = file_url.split(marker_object, 1)[1]

    if not path:
        return file_url

    sign_url = f"{SUPABASE_URL}/storage/v1/object/sign/logs-files/{path}"
    response = requests.post(
        sign_url,
        headers=_supabase_headers(),
        json={"expiresIn": 60 * 60 * 24 * 30},
        timeout=10,
    )
    if response.status_code not in (200, 201):
        return file_url

    signed = response.json().get("signedURL")
    if not signed:
        return file_url

    if signed.startswith("http"):
        return signed
    return f"{SUPABASE_URL}{signed}"


def admin_logs_ui():
    st.subheader("📜 Admin Logs Dashboard")

    if not st.session_state.get("is_admin"):
        st.error("Access Denied")
        return

    if "logs_page" not in st.session_state:
        st.session_state.logs_page = 1
    if "logs_page_size" not in st.session_state:
        st.session_state.logs_page_size = 10

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        search = c1.text_input("Search", placeholder="Username / Module / Action")

        try:
            usernames, modules = _fetch_filter_options()
        except Exception as ex:
            st.error(f"Failed to load filter options: {ex}")
            usernames, modules = [], []

        username_filter = c2.selectbox("Username", [""] + usernames, format_func=lambda x: x or "All Users")
        module_filter = c3.selectbox("Module", [""] + modules, format_func=lambda x: x or "All Modules")

        c4, c5, c6 = st.columns(3)
        action_filter = c4.text_input("Action")
        start_date = c5.date_input("Start date", value=None)
        end_date = c6.date_input("End date", value=None)

        st.session_state.logs_page_size = st.selectbox("Rows per page", [10, 20], index=[10, 20].index(st.session_state.logs_page_size))

    with st.spinner("Loading logs..."):
        try:
            rows, total_count = _fetch_logs(
                st.session_state.logs_page,
                st.session_state.logs_page_size,
                username_filter,
                module_filter,
                action_filter,
                search,
                start_date,
                end_date,
            )
        except Exception as ex:
            st.error(f"Failed to fetch logs: {ex}")
            return

    st.caption(f"Total Logs Count: {total_count}")

    if not rows:
        st.info("No Data Found")
        return

    now_utc = datetime.now(timezone.utc)
    for r in rows:
        created = r.get("created_at")
        if created:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            r["recent"] = (now_utc - dt) <= timedelta(hours=24)
        else:
            r["recent"] = False

    view_rows = []
    for r in rows:
        view_rows.append(
            {
                "Username": r.get("username", "-"),
                "Module": r.get("module", "-"),
                "Action": r.get("action", "-"),
                "Timestamp": r.get("created_at", "-"),
                "File": "Download" if r.get("file_url") else "-",
            }
        )

    df = pd.DataFrame(view_rows)
    st.dataframe(df, use_container_width=True)

    st.markdown("### File Downloads")
    for r in rows:
        if r.get("file_url"):
            download_url = _make_downloadable_url(r["file_url"])
            st.link_button(f"Download {r.get('file_name') or r.get('id')}", download_url)

    csv_df = pd.DataFrame(rows)[["username", "module", "action", "created_at", "file_name"]]
    csv_bytes = io.BytesIO()
    csv_df.to_csv(csv_bytes, index=False)
    st.download_button("Export CSV", csv_bytes.getvalue(), file_name="logs-filtered.csv", mime="text/csv")

    total_pages = max(1, (total_count + st.session_state.logs_page_size - 1) // st.session_state.logs_page_size)
    p1, p2, p3 = st.columns([1, 2, 1])
    if p1.button("Prev", disabled=st.session_state.logs_page <= 1):
        st.session_state.logs_page -= 1
        st.rerun()
    p2.markdown(f"<div style='text-align:center;padding-top:0.5rem;'>Page {st.session_state.logs_page} of {total_pages}</div>", unsafe_allow_html=True)
    if p3.button("Next", disabled=st.session_state.logs_page >= total_pages):
        st.session_state.logs_page += 1
        st.rerun()
