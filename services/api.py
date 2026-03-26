import streamlit as st
import requests

from services.auth import logout_user, TOKEN_EXPIRED_MESSAGE


def headers():
    return {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def _handle_auth_expiry(response):
    if response.status_code == 401:
        logout_user(TOKEN_EXPIRED_MESSAGE)
    return response


def get(url):
    return _handle_auth_expiry(requests.get(url, headers=headers()))

def post(url, body):
    return _handle_auth_expiry(requests.post(url, headers=headers(), json=body))

def put(url, body):
    return _handle_auth_expiry(requests.put(url, headers=headers(), json=body))

def delete(url):
    return _handle_auth_expiry(requests.delete(url, headers=headers()))
