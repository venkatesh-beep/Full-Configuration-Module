import streamlit as st


def module_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = (
        f"<div style='color:#6b7280; margin-top:0.35rem;'>{subtitle}</div>"
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:14px;
             padding:1rem 1.25rem; margin-bottom:1rem; box-shadow:0 4px 12px rgba(15,23,42,0.04);">
            <div style="font-size:1.45rem; font-weight:700; color:#0f172a;">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str) -> None:
    st.markdown(
        f"""
        <div style="margin:0.75rem 0 0.5rem 0; padding:0.45rem 0.75rem;
             background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
             font-weight:600; color:#0f172a;">
            {title}
        </div>
        """,
        unsafe_allow_html=True,
    )
