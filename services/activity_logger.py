import hashlib
import os
import base64
from datetime import datetime, timezone
from urllib.parse import urlparse, quote

import requests
import streamlit as st

SUPABASE_URL = "https://msyljqazsndtxpritfwy.supabase.co"
SUPABASE_KEY = "sb_publishable_HXoFqNveyeQcaFrL8suM1A_UBvL2rpZ"
SUPABASE_BUCKET = os.getenv("SUPABASE_LOG_BUCKET", "logs-files")

_original_request = requests.sessions.Session.request


def _supabase_headers(json_mode=True, extra=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    if json_mode:
        headers["Content-Type"] = "application/json"
    if extra:
        headers.update(extra)
    return headers


def upload_file_to_supabase(uploaded_file, module_name="Unknown"):
    if uploaded_file is None:
        return None, None

    file_bytes = uploaded_file.getvalue()
    if not file_bytes:
        return uploaded_file.name, None

    checksum = hashlib.md5(file_bytes).hexdigest()[:10]
    safe_module = module_name.lower().replace(" ", "-").replace("/", "-")
    ext = uploaded_file.name.split(".")[-1] if "." in uploaded_file.name else "bin"
    path = f"{safe_module}/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{checksum}.{ext}"

    encoded_path = quote(path, safe="/")
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{encoded_path}"
    headers = _supabase_headers(json_mode=False, extra={"x-upsert": "true", "Content-Type": uploaded_file.type or "application/octet-stream"})

    res = _original_request(requests.Session(), "PUT", upload_url, headers=headers, data=file_bytes, timeout=20)
    if res.status_code not in (200, 201):
        print(f"[Log Debug] file upload failed {res.status_code}: {res.text}")
        return uploaded_file.name, _build_data_url(uploaded_file.type, file_bytes)

    signed_url = _create_signed_file_url(encoded_path)
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"
    final_url = signed_url or public_url
    st.session_state.last_uploaded_file_name = uploaded_file.name
    st.session_state.last_uploaded_file_url = final_url
    print(f"[Log Debug] uploaded file to Supabase Storage: {final_url}")
    return uploaded_file.name, final_url


def _build_data_url(mime_type, file_bytes):
    if not file_bytes:
        return None
    safe_mime = mime_type or "application/octet-stream"
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{safe_mime};base64,{encoded}"


def _create_signed_file_url(encoded_path, expires_in=60 * 60 * 24 * 30):
    sign_endpoint = f"{SUPABASE_URL}/storage/v1/object/sign/{SUPABASE_BUCKET}/{encoded_path}"
    res = _original_request(
        requests.Session(),
        "POST",
        sign_endpoint,
        headers=_supabase_headers(),
        json={"expiresIn": expires_in},
        timeout=10,
    )
    if res.status_code not in (200, 201):
        print(f"[Log Debug] signed url generation failed {res.status_code}: {res.text}")
        return None

    signed_part = res.json().get("signedURL")
    if not signed_part:
        return None

    if signed_part.startswith("http"):
        return signed_part
    return f"{SUPABASE_URL}{signed_part}"


def log_action(action, module_name=None, file_name=None, file_url=None):
    username = st.session_state.get("username", "anonymous")
    module = module_name or st.session_state.get("active_module", "Unknown")

    if not file_name:
        file_name = st.session_state.get("last_uploaded_file_name")
    if not file_url:
        file_url = st.session_state.get("last_uploaded_file_url")

    payload = {
        "username": username,
        "module": module,
        "action": action,
        "file_name": file_name,
        "file_url": file_url,
        "ip_address": "127.0.0.1",
    }

    try:
        res = _original_request(
            requests.Session(),
            "POST",
            f"{SUPABASE_URL}/rest/v1/logs",
            headers=_supabase_headers(extra={"Prefer": "return=minimal"}),
            json=payload,
            timeout=10,
        )
        if res.status_code not in (200, 201):
            print(f"[Log Debug] log insert failed {res.status_code}: {res.text}")
        else:
            print(f"[Log Debug] log inserted: {module} | {action}")
    except Exception as ex:
        print(f"[Log Debug] log insert exception: {ex}")


def _request_with_logging(self, method, url, **kwargs):
    response = _original_request(self, method, url, **kwargs)
    try:
        if "supabase.co" in url:
            return response

        path = urlparse(url).path
        module = st.session_state.get("active_module", "Unknown")
        action = f"{method.upper()} {path} [{response.status_code}]"
        log_action(action=action, module_name=module)
    except Exception as ex:
        print(f"[Log Debug] request logging failed: {ex}")
    return response


def install_requests_logging():
    if getattr(requests.sessions.Session.request, "_logs_wrapped", False):
        return

    requests.sessions.Session.request = _request_with_logging
    requests.sessions.Session.request._logs_wrapped = True
    print("[Log Debug] Installed requests logging wrapper")


def install_file_uploader_logging():
    if getattr(st.file_uploader, "_logs_wrapped", False):
        return

    original_file_uploader = st.file_uploader

    def wrapped_file_uploader(*args, **kwargs):
        uploaded = original_file_uploader(*args, **kwargs)
        if uploaded is not None:
            module = st.session_state.get("active_module", "Unknown")
            name, file_url = upload_file_to_supabase(uploaded, module)
            log_action(action="FILE_UPLOAD", module_name=module, file_name=name, file_url=file_url)
        return uploaded

    wrapped_file_uploader._logs_wrapped = True
    st.file_uploader = wrapped_file_uploader
    print("[Log Debug] Installed file uploader logging wrapper")
