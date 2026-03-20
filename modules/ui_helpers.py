import streamlit as st


BRAND_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #f9fafb;
    --surface: #ffffff;
    --surface-soft: #f3f4f6;
    --surface-strong: #eef2ff;
    --border: #e5e7eb;
    --text: #111827;
    --muted: #6b7280;
    --primary: #4f46e5;
    --primary-dark: #4338ca;
    --primary-soft: #eef2ff;
    --shadow-sm: 0 6px 18px rgba(15, 23, 42, 0.06);
    --shadow-md: 0 14px 32px rgba(15, 23, 42, 0.08);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #f9fafb 0%, #f3f6fb 100%);
    color: var(--text);
}

.block-container {
    padding-top: 1.25rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

[data-testid="stSidebar"] * {
    color: #f9fafb;
}

[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start;
    border-radius: 12px;
    min-height: 2.8rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: transparent;
    color: #e5e7eb;
    box-shadow: none;
}

[data-testid="stSidebar"] .stButton > button:hover {
    border-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.24), rgba(79, 70, 229, 0.12));
    color: #ffffff;
    border-color: rgba(129, 140, 248, 0.5);
}

.dashboard-navbar {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(229, 231, 235, 0.9);
    border-radius: 18px;
    padding: 1rem 1.2rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1rem;
}

.dashboard-breadcrumb {
    color: var(--muted);
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
}

.dashboard-title {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--text);
    margin: 0;
}

.dashboard-subtitle {
    color: var(--muted);
    margin-top: 0.35rem;
    font-size: 0.95rem;
}

.profile-chip {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 0.65rem;
}

.profile-avatar {
    width: 40px;
    height: 40px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-soft);
    color: var(--primary-dark);
    font-weight: 700;
}

.profile-meta {
    text-align: right;
}

.profile-label {
    color: var(--muted);
    font-size: 0.78rem;
}

.profile-name {
    color: var(--text);
    font-size: 0.92rem;
    font-weight: 700;
}

.stats-card, .module-card, .content-shell, .quick-card, .empty-state {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow-sm);
}

.stats-card {
    padding: 1rem 1.1rem;
    min-height: 112px;
}

.stats-label {
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.stats-value {
    color: var(--text);
    font-size: 1.45rem;
    font-weight: 800;
    margin-top: 0.35rem;
}

.stats-note {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.3rem;
}

.section-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 1rem;
    margin: 1.15rem 0 0.75rem;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text);
}

.section-copy {
    color: var(--muted);
    font-size: 0.92rem;
    margin-top: 0.2rem;
}

.module-card {
    padding: 1rem;
    min-height: 220px;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.module-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.module-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-soft);
    font-size: 1.2rem;
    margin-bottom: 0.85rem;
}

.module-group {
    color: var(--primary);
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.module-title {
    color: var(--text);
    font-weight: 700;
    font-size: 1.04rem;
    margin-top: 0.4rem;
}

.module-copy {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.45rem;
    min-height: 56px;
}

.quick-card {
    padding: 1rem 1.1rem;
}

.quick-title {
    color: var(--text);
    font-size: 0.98rem;
    font-weight: 700;
}

.quick-copy {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.25rem;
}

.content-shell {
    padding: 1.2rem;
    margin-top: 1rem;
}

.content-kicker {
    color: var(--primary);
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.content-title {
    color: var(--text);
    font-size: 1.2rem;
    font-weight: 800;
    margin-top: 0.35rem;
}

.content-copy {
    color: var(--muted);
    font-size: 0.92rem;
    margin-top: 0.25rem;
}

.empty-state {
    padding: 1.4rem;
    text-align: center;
}

.empty-title {
    color: var(--text);
    font-weight: 700;
    font-size: 1rem;
}

.empty-copy {
    color: var(--muted);
    font-size: 0.92rem;
    margin-top: 0.25rem;
}

div[data-testid="stTooltipHoverTarget"] {
    width: 100%;
}

@media (max-width: 1024px) {
    .dashboard-title {
        font-size: 1.4rem;
    }
}
</style>
"""


def inject_brand_styles() -> None:
    st.markdown(BRAND_STYLES, unsafe_allow_html=True)


def module_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<div class='content-copy'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="content-shell">
            <div class="content-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str) -> None:
    st.markdown(
        f"""
        <div class="section-row" style="margin-top:0.85rem;margin-bottom:0.5rem;">
            <div class="section-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
