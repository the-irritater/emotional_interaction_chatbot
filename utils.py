"""
Utility Functions
=================
Helper functions for participant ID generation, response persistence,
question list construction, and CSS injection.
"""

import base64
import csv
import os
import uuid
from datetime import datetime
from collections import OrderedDict
from functools import lru_cache
from typing import Optional

from questions import LIKERT_LABELS, SECTION_BACKGROUNDS


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_BASE_DIR, "data")
ASSETS_DIR = os.path.join(_BASE_DIR, "assets")
CSV_PATH = os.path.join(DATA_DIR, "responses.csv")

CSV_COLUMNS = [
    "participant_id",
    "group",
    "section",
    "question_id",
    "question_text",
    "response",
    "response_label",
    "timestamp",
]

# Map background theme keys to image filenames in assets/
_BG_IMAGE_MAP = {
    "capability": "bg_capability.png",
    "motivation": "bg_capability.png",   # shares the futuristic AI theme
    "authenticity": "bg_authenticity.png",
    "openness": "bg_openness.png",
    "empathy": "bg_openness.png",        # shares the optimistic theme
    "concerns": "bg_concerns.png",
    "trust": "bg_trust.png",
}


# ---------------------------------------------------------------------------
# Participant ID
# ---------------------------------------------------------------------------
def generate_participant_id() -> str:
    """Generate a unique, anonymous participant identifier."""
    return f"P-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Question list builder
# ---------------------------------------------------------------------------
def build_question_list(sections: OrderedDict) -> list:
    """
    Flatten an ordered dict of sections into a sequential list of question
    dicts, each carrying section metadata.

    Returns
    -------
    list[dict]
        Each dict: {
            "id": "section_key_Q1",
            "section_key": str,
            "section_title": str,
            "background": str,
            "text": str,
            "index_in_section": int,
            "global_index": int,
        }
    """
    flat = []
    global_idx = 0
    for section_key, section_data in sections.items():
        for local_idx, q_text in enumerate(section_data["questions"]):
            flat.append({
                "id": f"{section_key}_Q{local_idx + 1}",
                "section_key": section_key,
                "section_title": section_data["title"],
                "background": section_data["background"],
                "text": q_text,
                "index_in_section": local_idx,
                "global_index": global_idx,
            })
            global_idx += 1
    return flat


# ---------------------------------------------------------------------------
# Likert helpers
# ---------------------------------------------------------------------------
def get_likert_label(value: int) -> str:
    """Return the text label for a numeric Likert value."""
    return LIKERT_LABELS.get(value, str(value))


# ---------------------------------------------------------------------------
# Data persistence (Google Sheets + CSV — dual save)
# ---------------------------------------------------------------------------
def ensure_data_dir():
    """Create the data directory if it does not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def _save_to_google_sheets(rows: list[dict]) -> bool:
    """
    Append rows to Google Sheets using gspread directly.
    Returns True on success, False on failure.
    Uses append_rows() which is atomic — no risk of overwriting existing data.
    """
    import streamlit as st

    try:
        # Check if secrets are configured
        if "connections" not in st.secrets or "gsheets" not in st.secrets.connections:
            print("Google Sheets: No connection configured in secrets.toml")
            return False

        gsheets_config = st.secrets["connections"]["gsheets"]
        spreadsheet_url = gsheets_config.get("spreadsheet", "")

        # Build service account info dict
        sa = gsheets_config.get("service_account", {})
        if not sa:
            print("Google Sheets: No service_account in secrets.toml")
            return False

        service_account_info = {
            "type": sa.get("type", "service_account"),
            "project_id": sa.get("project_id", ""),
            "private_key_id": sa.get("private_key_id", ""),
            "private_key": sa.get("private_key", ""),
            "client_email": sa.get("client_email", ""),
            "client_id": sa.get("client_id", ""),
            "auth_uri": sa.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": sa.get("token_uri", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": sa.get("auth_provider_x509_cert_url", ""),
            "client_x509_cert_url": sa.get("client_x509_cert_url", ""),
            "universe_domain": sa.get("universe_domain", "googleapis.com"),
        }

        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.sheet1

        # Check if headers exist; if sheet is empty, write headers first
        existing = worksheet.get_all_values()
        if not existing:
            worksheet.update('A1', [CSV_COLUMNS])

        # Convert rows to list-of-lists in column order
        value_rows = []
        for row in rows:
            value_rows.append([str(row.get(col, "")) for col in CSV_COLUMNS])

        # Append (atomic — does NOT overwrite existing data)
        worksheet.append_rows(
            value_rows,
            value_input_option="USER_ENTERED",
        )

        print(f"✅ Google Sheets: Saved {len(value_rows)} rows successfully")
        return True

    except Exception as e:
        print(f"❌ Google Sheets save failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _save_to_csv(rows: list[dict]):
    """Append rows to the local CSV file."""
    ensure_data_dir()
    file_exists = os.path.isfile(CSV_PATH) and os.path.getsize(CSV_PATH) > 0

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"✅ Local CSV: Saved {len(rows)} rows to {CSV_PATH}")


def save_responses_to_csv(
    participant_id: str,
    group: str,
    responses: dict,
):
    """
    Save responses to BOTH Google Sheets AND local CSV.
    Google Sheets is the primary store; CSV is always kept as backup.
    """
    rows = []
    for q_id, data in responses.items():
        rows.append({
            "participant_id": participant_id,
            "group": group,
            "section": data["section"],
            "question_id": q_id,
            "question_text": data["question"],
            "response": data["response"],
            "response_label": get_likert_label(data["response"]),
            "timestamp": data["timestamp"],
        })

    # Always try Google Sheets first
    sheets_ok = _save_to_google_sheets(rows)

    # Always save to local CSV as backup
    _save_to_csv(rows)


# ---------------------------------------------------------------------------
# Background image helpers
# ---------------------------------------------------------------------------
@lru_cache(maxsize=10)
def _load_bg_image_b64(filename: str) -> Optional[str]:
    """Load a background image from assets/ and return as base64 string."""
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# CSS injection helpers
# ---------------------------------------------------------------------------
def get_background_gradient(background_key: str) -> str:
    """Return the CSS gradient string for a given background theme key."""
    return SECTION_BACKGROUNDS.get(
        background_key,
        "linear-gradient(135deg, #0e1117 0%, #1a1a2e 100%)",
    )


def build_background_css(background_key: str) -> str:
    """
    Return a <style> block that sets the Streamlit app background
    to match the current questionnaire section.
    Uses a background image layered over a gradient for rich texture.
    """
    gradient = get_background_gradient(background_key)

    # Try to load a matching background image
    img_file = _BG_IMAGE_MAP.get(background_key)
    img_b64 = _load_bg_image_b64(img_file) if img_file else None

    if img_b64:
        return f"""
        <style>
            .stApp {{
                background: {gradient};
                background-image: url("data:image/png;base64,{img_b64}");
                background-size: cover;
                background-position: center;
                background-blend-mode: soft-light;
                transition: background 1s cubic-bezier(0.4, 0, 0.2, 1);
            }}
        </style>
        """
    else:
        return f"""
        <style>
            .stApp {{
                background: {gradient};
                transition: background 1s cubic-bezier(0.4, 0, 0.2, 1);
            }}
        </style>
        """


# ---------------------------------------------------------------------------
# Main custom CSS for the entire app
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ── Typography ────────────────────────────────────────────────────── */
*, html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Hide Streamlit chrome ─────────────────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

/* ── Default background ────────────────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #0e1117 0%, #1a1a2e 100%);
    transition: background 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Chat message bubbles ──────────────────────────────────────────── */
.stChatMessage {
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Fade-in animation ─────────────────────────────────────────────── */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

@keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50%      { opacity: 1; }
}

/* ── Likert scale buttons ──────────────────────────────────────────── */
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.06) !important;
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    min-height: 52px !important;
    padding: 0.5rem 0.25rem !important;
    line-height: 1.3 !important;
}

.stButton > button:hover {
    background: rgba(255, 255, 255, 0.18) !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
    background: rgba(255, 255, 255, 0.25) !important;
}

/* ── Progress bar ──────────────────────────────────────────────────── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 8px !important;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stProgress > div > div {
    background: rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
}

/* ── Welcome screen elements ───────────────────────────────────────── */
.welcome-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    max-width: 640px;
    margin: 2rem auto;
    text-align: center;
    animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.welcome-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
    line-height: 1.2;
}

.welcome-subtitle {
    font-size: 1.05rem;
    color: rgba(255, 255, 255, 0.65);
    line-height: 1.7;
    margin: 1rem 0 1.5rem;
}

.consent-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin: 1.5rem auto;
    max-width: 480px;
    font-size: 0.88rem;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.6;
    text-align: left;
}

.consent-box .consent-icon {
    font-size: 1.3rem;
    margin-right: 0.5rem;
}

/* ── Completion screen ─────────────────────────────────────────────── */
.completion-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    max-width: 580px;
    margin: 3rem auto;
    text-align: center;
    animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.completion-check {
    font-size: 3.5rem;
    margin-bottom: 1rem;
    animation: fadeIn 1s ease;
}

.completion-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #43e97b, #38f9d7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}

.completion-text {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.7;
    margin: 1rem 0;
}

.saved-badge {
    display: inline-block;
    background: rgba(67, 233, 123, 0.12);
    border: 1px solid rgba(67, 233, 123, 0.25);
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-size: 0.85rem;
    color: rgba(67, 233, 123, 0.9);
    margin-top: 1rem;
}

/* ── Section header ────────────────────────────────────────────────── */
.section-header {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1rem;
    text-align: center;
    animation: fadeIn 0.6s ease;
}

.section-header h3 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.75);
    letter-spacing: 0.02em;
}

/* ── Scale reference row ───────────────────────────────────────────── */
.scale-ref {
    display: flex;
    justify-content: space-between;
    padding: 0 4px;
    margin-bottom: 8px;
    font-size: 0.72rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* ── Progress label ────────────────────────────────────────────────── */
.progress-label {
    text-align: center;
    font-size: 0.78rem;
    color: rgba(255, 255, 255, 0.45);
    margin-top: 4px;
    margin-bottom: 1rem;
    letter-spacing: 0.02em;
}

/* ── Screening buttons ─────────────────────────────────────────────── */
.screening-btn .stButton > button {
    min-height: 48px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    border-radius: 14px !important;
    background: rgba(102, 126, 234, 0.15) !important;
    border-color: rgba(102, 126, 234, 0.3) !important;
}

.screening-btn .stButton > button:hover {
    background: rgba(102, 126, 234, 0.3) !important;
    border-color: rgba(102, 126, 234, 0.5) !important;
}

/* ── Typing indicator dots ─────────────────────────────────────────── */
.typing-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.5);
    margin: 0 3px;
    animation: pulse 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

/* ── Divider ───────────────────────────────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin: 1rem 0;
}

/* ── Mobile responsiveness ─────────────────────────────────────────── */
@media (max-width: 640px) {
    .welcome-card, .completion-card {
        padding: 2rem 1.25rem;
        margin: 1rem 0.5rem;
    }
    .welcome-title {
        font-size: 1.6rem;
    }
    .stButton > button {
        min-height: 44px !important;
        font-size: 0.75rem !important;
        padding: 0.4rem 0.15rem !important;
    }
    .scale-ref {
        font-size: 0.6rem;
    }
}
</style>
"""
