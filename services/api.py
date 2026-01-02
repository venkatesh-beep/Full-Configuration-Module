import streamlit as st
import requests

def headers():
    return {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def get(url):
    return requests.get(url, headers=headers())

def post(url, body):
    return requests.post(url, headers=headers(), json=body)

def put(url, body):
    return requests.put(url, headers=headers(), json=body)

def delete(url):
    return requests.delete(url, headers=headers())
