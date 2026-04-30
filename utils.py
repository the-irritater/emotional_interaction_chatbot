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
from typing import Dict, List, Optional

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
    "started_at",
    "completed_at",
    "duration_seconds",
]

PARTICIPANT_COLUMNS = [
    "participant_id",
    "group",
    "started_at",
    "completed_at",
    "duration_seconds",
    "total_questions",
    "total_answered",
    "submission_status",
    "timestamp",
]

# Map background theme keys to image filenames in assets/
_BG_IMAGE_MAP = {
    "capability": "bg_capability.png",
    "motivation": "bg_capability.png",   # shares the futuristic AI theme
    "personality": "bg_capability.png",  # shares the futuristic AI theme
    "authenticity": "bg_authenticity.png",
    "openness": "bg_openness.png",
    "empathy": "bg_openness.png",        # shares the optimistic theme
    "concerns": "bg_concerns.png",
    "trust": "bg_trust.png",
    "usage": "bg_trust.png",             # shares the trust theme
    "comparison": "bg_authenticity.png", # shares the authenticity theme
    "future": "bg_openness.png",         # shares the optimistic theme
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
            "total_in_section": int,
            "global_index": int,
        }
    """
    flat = []
    global_idx = 0
    for section_key, section_data in sections.items():
        total_in_section = len(section_data["questions"])
        for local_idx, q_text in enumerate(section_data["questions"]):
            flat.append({
                "id": f"{section_key}_Q{local_idx + 1}",
                "section_key": section_key,
                "section_title": section_data["title"],
                "background": section_data["background"],
                "scale": section_data.get("scale", "likert"),
                "text": q_text,
                "index_in_section": local_idx,
                "total_in_section": total_in_section,
                "global_index": global_idx,
            })
            global_idx += 1
    return flat


def get_section_list(sections: OrderedDict) -> list:
    """Return a list of section dicts with keys and titles for progress display."""
    return [
        {"key": key, "title": data["title"]}
        for key, data in sections.items()
    ]


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


def _get_gsheets_client():
    """
    Build and return (gc, spreadsheet) using gspread + service account.
    Returns (gc, spreadsheet) on success, raises on failure.
    """
    import streamlit as st
    import gspread
    from google.oauth2.service_account import Credentials

    gsheets_config = st.secrets["connections"]["gsheets"]
    spreadsheet_url = gsheets_config["spreadsheet"]
    sa = gsheets_config["service_account"]

    service_account_info = {
        "type": sa["type"],
        "project_id": sa["project_id"],
        "private_key_id": sa["private_key_id"],
        "private_key": sa["private_key"],
        "client_email": sa["client_email"],
        "client_id": sa["client_id"],
        "auth_uri": sa["auth_uri"],
        "token_uri": sa["token_uri"],
        "auth_provider_x509_cert_url": sa["auth_provider_x509_cert_url"],
        "client_x509_cert_url": sa["client_x509_cert_url"],
        "universe_domain": sa["universe_domain"],
    }

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_url(spreadsheet_url)
    return gc, spreadsheet


def _save_to_google_sheets(rows: List[Dict]) -> tuple:
    """
    Append rows to Google Sheets using gspread directly.
    Returns (True, "") on success, (False, error_msg) on failure.
    Uses append_rows() which is atomic — no risk of overwriting existing data.
    """
    try:
        gc, spreadsheet = _get_gsheets_client()
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
        return True, ""

    except Exception as e:
        err = f"❌ Google Sheets save failed: {e}"
        print(err)
        import traceback
        traceback.print_exc()
        return False, str(e)


def _save_participant_summary(summary: Dict) -> tuple:
    """
    Save a participant summary row to the 'Participants' worksheet.
    Creates the worksheet if it doesn't exist.
    Returns (True, "") on success, (False, error_msg) on failure.
    """
    try:
        gc, spreadsheet = _get_gsheets_client()

        # Get or create Participants worksheet
        try:
            ws = spreadsheet.worksheet("Participants")
        except Exception:
            ws = spreadsheet.add_worksheet(
                title="Participants", rows=1000, cols=len(PARTICIPANT_COLUMNS)
            )
            ws.update('A1', [PARTICIPANT_COLUMNS])

        # Append summary row
        row_values = [str(summary.get(col, "")) for col in PARTICIPANT_COLUMNS]
        ws.append_rows(
            [row_values],
            value_input_option="USER_ENTERED",
        )
        print(f"✅ Participant summary saved for {summary.get('participant_id')}")
        return True, ""

    except Exception as e:
        err = f"❌ Participant summary save failed: {e}"
        print(err)
        return False, str(e)


def _save_to_csv(rows: List[Dict]):
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
    started_at: str = "",
    completed_at: str = "",
    duration_seconds: str = "",
) -> tuple:
    """
    Save responses to BOTH Google Sheets AND local CSV.
    Google Sheets is the primary store; CSV is always kept as backup.
    Returns (sheets_ok, error_message).
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
            "response_label": get_likert_label(data["response"]) if isinstance(data["response"], int) else data["response"],
            "timestamp": data["timestamp"],
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": duration_seconds,
        })

    # Always try Google Sheets first
    sheets_ok, error_msg = _save_to_google_sheets(rows)

    # Always save to local CSV as backup
    _save_to_csv(rows)

    # Save participant summary
    total_q = len([r for r in responses if not r.startswith("demo_") and r != "screening" and r != "open_ended_Q1"])
    _save_participant_summary({
        "participant_id": participant_id,
        "group": group,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "total_questions": str(total_q),
        "total_answered": str(len(responses)),
        "submission_status": "cloud_saved" if sheets_ok else "local_only",
        "timestamp": datetime.now().isoformat(),
    })

    return sheets_ok, error_msg


def save_single_response(
    participant_id: str,
    group: str,
    q_id: str,
    data: dict,
    started_at: str = "",
) -> tuple:
    """
    Autosave a single response immediately for session recovery.
    Returns (sheets_ok, error_message).
    """
    rows = [{
        "participant_id": participant_id,
        "group": group,
        "section": data["section"],
        "question_id": q_id,
        "question_text": data["question"],
        "response": data["response"],
        "response_label": get_likert_label(data["response"]) if isinstance(data["response"], int) else data["response"],
        "timestamp": data["timestamp"],
        "started_at": started_at,
        "completed_at": "",
        "duration_seconds": "",
    }]

    sheets_ok, error_msg = _save_to_google_sheets(rows)
    _save_to_csv(rows)
    return sheets_ok, error_msg


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
        "linear-gradient(135deg, #0a0e27 0%, #1a1a2e 100%)",
    )


def build_background_css(background_key: str) -> str:
    """
    Return a <style> block that guarantees the clean dark background
    from the sleek UI mockup, ignoring dynamic section backgrounds.
    """
    return f"""
    <style>
        .stApp {{
            background-color: #050614 !important;
            background-image: none !important;
        }}
    </style>
    """


# ---------------------------------------------------------------------------
# Progress ring SVG builder
# ---------------------------------------------------------------------------
def build_progress_ring(percent: int) -> str:
    """
    Build an SVG circular progress ring.
    Returns an HTML string with the ring and percentage text.
    """
    radius = 70
    stroke_width = 8
    circumference = 2 * 3.14159 * radius
    offset = circumference - (percent / 100) * circumference

    return f"""
    <div style="display:flex; justify-content:center; margin: 1.5rem 0;">
        <svg width="180" height="180" viewBox="0 0 180 180">
            <defs>
                <linearGradient id="progressGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#7c3aed;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#a855f7;stop-opacity:1" />
                </linearGradient>
            </defs>
            <!-- Background circle -->
            <circle cx="90" cy="90" r="{radius}"
                    fill="none"
                    stroke="rgba(255,255,255,0.08)"
                    stroke-width="{stroke_width}"/>
            <!-- Progress arc -->
            <circle cx="90" cy="90" r="{radius}"
                    fill="none"
                    stroke="url(#progressGrad)"
                    stroke-width="{stroke_width}"
                    stroke-linecap="round"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{offset}"
                    transform="rotate(-90 90 90)"
                    style="transition: stroke-dashoffset 0.8s ease;"/>
            <!-- Percentage text -->
            <text x="90" y="82" text-anchor="middle"
                  fill="white" font-size="32" font-weight="700"
                  font-family="Inter, sans-serif">{percent}%</text>
            <text x="90" y="105" text-anchor="middle"
                  fill="rgba(255,255,255,0.5)" font-size="12" font-weight="500"
                  font-family="Inter, sans-serif">Completed</text>
        </svg>
    </div>
    """


def build_section_progress_html(sections: list, current_section_key: str, completed_sections: set) -> str:
    """
    Build HTML for a section-by-section progress list.
    Each section shows: number, title, and status (Completed/In Progress/Upcoming).
    """
    items_html = ""
    for i, sec in enumerate(sections):
        key = sec["key"]
        title = sec["title"]
        num = i + 1

        if key in completed_sections:
            status_class = "completed"
            status_text = "Completed"
            icon = "✓"
            icon_bg = "rgba(74, 222, 128, 0.15)"
            icon_color = "#4ade80"
        elif key == current_section_key:
            status_class = "in-progress"
            status_text = "In Progress"
            icon = str(num)
            icon_bg = "rgba(124, 58, 237, 0.25)"
            icon_color = "#a855f7"
        else:
            status_class = "upcoming"
            status_text = "Upcoming"
            icon = str(num)
            icon_bg = "rgba(255, 255, 255, 0.06)"
            icon_color = "rgba(255,255,255,0.35)"

        items_html += f"""
        <div class="section-progress-item {status_class}">
            <div class="section-progress-icon" style="background:{icon_bg}; color:{icon_color};">
                {icon}
            </div>
            <div class="section-progress-info">
                <span class="section-progress-title">{title}</span>
                <span class="section-progress-status">{status_text}</span>
            </div>
        </div>
        """

    return f'<div class="section-progress-list">{items_html}</div>'


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
    background-color: #050614 !important;
    padding-bottom: 5rem !important;
}

/* ── Stars / ambient particles ─────────────────────────────────────── */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.1) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 50% 10%, rgba(168,85,247,0.15) 0%, transparent 100%),
        radial-gradient(1px 1px at 70% 80%, rgba(255,255,255,0.08) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 85% 15%, rgba(168,85,247,0.08) 0%, transparent 100%);
    pointer-events: none;
    z-index: 0;
}

/* ── Fade-in animations ────────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

@keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50%      { opacity: 1; }
}

/* ── Chat message bubbles ──────────────────────────────────────────── */
.stChatMessage {
    background: #0D1022 !important;
    border: 1px solid rgba(168, 85, 247, 0.15) !important;
    border-radius: 16px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* User bubbles differentiation */
.stChatMessage:nth-child(even) {
    background: #14112B !important; /* slightly purpleish for user */
    border-color: rgba(168, 85, 247, 0.25) !important;
}

/* ── Likert scale buttons & General Buttons ────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    border: 1px solid rgba(168, 85, 247, 0.25) !important;
    background: #0F122B !important;
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    min-height: 48px !important;
}

div[data-testid="column"] .stButton > button {
    /* For Likert scale columns specifically, make them more boxy */
    aspect-ratio: 1 !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    background: #0B0E23 !important;
}

.stButton > button:hover {
    background: #1C153E !important;
    border-color: #C084FC !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
    background: #C084FC !important;
    color: white !important;
}

/* ── Start / Action buttons ────────────────────────────────────────── */
.start-btn .stButton > button,
.action-btn .stButton > button,
.next-btn .stButton > button,
.screening-btn .stButton > button {
    background: linear-gradient(90deg, #9F5FFC 0%, #D45DF8 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    border-radius: 12px !important;
    min-height: 50px !important;
    box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4) !important;
    transition: all 0.3s ease !important;
}

.start-btn .stButton > button:hover,
.action-btn .stButton > button:hover,
.next-btn .stButton > button:hover,
.screening-btn .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6) !important;
}

/* ── Back button ───────────────────────────────────────────────────── */
.back-btn .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: rgba(255, 255, 255, 0.7) !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    min-height: 48px !important;
    border-radius: 12px !important;
}

.back-btn .stButton > button:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    color: white !important;
}

/* ── Skip button ───────────────────────────────────────────────────── */
.skip-btn .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: rgba(255, 255, 255, 0.45) !important;
    font-weight: 400 !important;
    font-size: 0.85rem !important;
    min-height: 40px !important;
}

.skip-btn .stButton > button:hover {
    background: rgba(255, 255, 255, 0.04) !important;
    color: rgba(255, 255, 255, 0.65) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Screening buttons ─────────────────────────────────────────────── */
.screening-btn .stButton > button {
    min-height: 52px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    border-radius: 14px !important;
    background: rgba(124, 58, 237, 0.12) !important;
    border-color: rgba(124, 58, 237, 0.25) !important;
}

.screening-btn .stButton > button:hover {
    background: rgba(124, 58, 237, 0.28) !important;
    border-color: rgba(168, 85, 247, 0.5) !important;
}

/* ── Progress bar ──────────────────────────────────────────────────── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #9F5FFC 0%, #D45DF8 100%) !important;
    border-radius: 8px !important;
}

.stProgress > div > div {
    background: rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    height: 6px !important;
}

/* ── Welcome screen ────────────────────────────────────────────────── */
.welcome-card {
    background: #090A1A;
    border: 1px solid #1C2042;
    border-radius: 24px;
    padding: 0 0 2rem 0; /* image at top needs 0 padding */
    max-width: 500px;
    margin: 1.5rem auto;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.6s ease;
}

.hero-image {
    width: 100%;
    height: 220px;
    object-fit: cover;
    margin-bottom: 2rem;
    border-bottom: 1px solid #1C2042;
}

.welcome-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: white;
    margin-bottom: 0.5rem;
    padding: 0 2rem;
    line-height: 1.25;
}

.welcome-subtitle {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.65);
    line-height: 1.6;
    margin: 0.5rem 2rem 1.5rem;
}

/* ── Info strip bullets ────────────────────────────────────────────── */
.info-strip {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 0 2rem 2rem;
}

.info-strip-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: #11142A;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: white;
    text-align: left;
}

.info-strip-icon {
    width: 24px;
    height: 24px;
    min-width: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ── Consent box ───────────────────────────────────────────────────── */
.consent-box {
    background: rgba(124, 58, 237, 0.06);
    border: 1px solid rgba(124, 58, 237, 0.12);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin: 1.5rem auto;
    max-width: 480px;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.55);
    line-height: 1.6;
    text-align: left;
}

/* ── Completion screen ─────────────────────────────────────────────── */
.completion-card {
    background: #090A1A;
    border: 1px solid #1C2042;
    border-radius: 24px;
    padding: 3rem 2.5rem;
    max-width: 500px;
    margin: 2rem auto;
    text-align: center;
    animation: fadeInUp 0.6s ease;
}

.completion-card.success {
    background: #090A1A;
    border: 1px solid #1C2042;
}

.completion-card.warning {
    background: rgba(251, 191, 36, 0.03);
    border: 1px solid rgba(251, 191, 36, 0.15);
}

.completion-check {
    width: 80px;
    height: 80px;
    margin: 0 auto 1.25rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    animation: fadeIn 1s ease;
}

.completion-check.success {
    background: linear-gradient(135deg, #a855f7, #7c3aed) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 0 30px rgba(168, 85, 247, 0.6);
}

.completion-check.warning {
    background: rgba(251, 191, 36, 0.1);
    border: 2px solid rgba(251, 191, 36, 0.3);
}

.completion-title {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.completion-title.success {
    color: white !important;
}

.completion-title.warning {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.completion-text {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.7;
    margin: 0.75rem 0;
}

.saved-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: 12px;
    padding: 0.65rem 1.25rem;
    font-size: 0.85rem;
    margin-top: 1rem;
}

.saved-badge.success {
    background: rgba(168, 85, 247, 0.08);
    border: 1px solid rgba(168, 85, 247, 0.2);
    color: rgba(168, 85, 247, 0.9);
}

.saved-badge.warning {
    background: rgba(251, 191, 36, 0.08);
    border: 1px solid rgba(251, 191, 36, 0.2);
    color: rgba(251, 191, 36, 0.9);
}

/* ── Section header ────────────────────────────────────────────────── */
.section-header {
    background: rgba(124, 58, 237, 0.08);
    border: 1px solid rgba(124, 58, 237, 0.15);
    border-radius: 14px;
    padding: 0.85rem 1.25rem;
    margin-bottom: 1rem;
    text-align: center;
    animation: fadeIn 0.6s ease;
}

.section-header h3 {
    margin: 0;
    font-size: 0.92rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.8);
    letter-spacing: 0.02em;
}

.section-header .section-tag {
    display: inline-block;
    background: rgba(124, 58, 237, 0.15);
    color: #c084fc;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Scale reference row ───────────────────────────────────────────── */
.scale-ref {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
    margin-bottom: 6px;
    font-size: 0.72rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.scale-ref-center {
    color: rgba(255, 255, 255, 0.3);
}

/* ── Likert label row (mobile-visible) ─────────────────────────────── */
.likert-labels-row {
    display: none;
    flex-direction: column;
    gap: 0.35rem;
    margin-top: 0.5rem;
    padding: 0.75rem;
    background: rgba(124, 58, 237, 0.05);
    border-radius: 10px;
    border: 1px solid rgba(124, 58, 237, 0.08);
}

.likert-label-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.72rem;
    color: rgba(255, 255, 255, 0.45);
}

.likert-label-num {
    width: 20px;
    height: 20px;
    min-width: 20px;
    border-radius: 5px;
    background: rgba(124, 58, 237, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.7rem;
    color: #c084fc;
}

/* ── Mobile tap hint ───────────────────────────────────────────────── */
.tap-hint {
    text-align: center;
    font-size: 0.72rem;
    color: rgba(255, 255, 255, 0.25);
    margin-top: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
}

.tap-hint-icon {
    font-size: 0.8rem;
}

/* ── Progress label ────────────────────────────────────────────────── */
.progress-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.9);
    margin-top: 8px;
    margin-bottom: 1.5rem;
    font-weight: 500;
}

.progress-percent {
    font-weight: 700;
    color: white;
}

/* ── Section progress list (interstitial) ──────────────────────────── */
.section-progress-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 1rem auto;
    max-width: 400px;
}

.section-progress-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.85rem;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    transition: all 0.3s ease;
}

.section-progress-item.completed {
    background: rgba(74, 222, 128, 0.04);
    border-color: rgba(74, 222, 128, 0.1);
}

.section-progress-item.in-progress {
    background: rgba(124, 58, 237, 0.06);
    border-color: rgba(124, 58, 237, 0.15);
}

.section-progress-icon {
    width: 32px;
    height: 32px;
    min-width: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
}

.section-progress-info {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.section-progress-title {
    font-size: 0.82rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.75);
}

.section-progress-status {
    font-size: 0.7rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.35);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.section-progress-item.completed .section-progress-status {
    color: rgba(74, 222, 128, 0.7);
}

.section-progress-item.in-progress .section-progress-status {
    color: rgba(168, 85, 247, 0.8);
}

/* ── Encouragement message ─────────────────────────────────────────── */
.encouragement {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1rem;
    padding: 0.65rem 1rem;
    background: rgba(124, 58, 237, 0.06);
    border-radius: 12px;
    border: 1px solid rgba(124, 58, 237, 0.1);
    font-size: 0.82rem;
    color: rgba(255, 255, 255, 0.55);
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
}

.encouragement-icon {
    font-size: 1rem;
    color: #c084fc;
}

/* ── Typing indicator dots ─────────────────────────────────────────── */
.typing-dots span {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(168, 85, 247, 0.6);
    margin: 0 3px;
    animation: pulse 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

/* ── Divider ───────────────────────────────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid rgba(124, 58, 237, 0.08);
    margin: 1rem 0;
}

/* ── Select box styling ────────────────────────────────────────────── */
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(124, 58, 237, 0.15) !important;
    border-radius: 12px !important;
    color: white !important;
}

/* ── Text input styling ────────────────────────────────────────────── */
.stTextArea textarea, .stTextInput input {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(124, 58, 237, 0.15) !important;
    border-radius: 12px !important;
    color: white !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(124, 58, 237, 0.4) !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.1) !important;
}

/* ── Download button ───────────────────────────────────────────────── */
.stDownloadButton > button {
    background: rgba(124, 58, 237, 0.1) !important;
    border: 1px solid rgba(124, 58, 237, 0.2) !important;
    color: #c084fc !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
}

.stDownloadButton > button:hover {
    background: rgba(124, 58, 237, 0.2) !important;
    border-color: rgba(168, 85, 247, 0.4) !important;
}

/* ── Mobile responsiveness ─────────────────────────────────────────── */
@media (max-width: 768px) {
    .welcome-card, .completion-card {
        padding: 2rem 1.25rem;
        margin: 1rem 0.5rem;
        border-radius: 20px;
    }
    .welcome-title {
        font-size: 1.55rem;
    }
    .welcome-subtitle {
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .consent-box {
        line-height: 1.6;
    }
    .info-strip {
        max-width: 100%;
    }
    .start-btn .stButton > button, .action-btn .stButton > button {
        width: 100% !important;
    }
    .stButton > button {
        min-height: 48px !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.2rem !important;
    }
    .scale-ref {
        font-size: 0.65rem;
    }
    /* Show full Likert labels on mobile */
    .likert-labels-row {
        display: flex !important;
    }
    .section-progress-list {
        max-width: 100%;
    }
}

@media (max-width: 480px) {
    .welcome-card, .completion-card {
        padding: 1.5rem 1rem;
        margin: 0.5rem 0.25rem;
    }
    .welcome-title {
        font-size: 1.35rem;
    }
    .stButton > button {
        min-height: 44px !important;
        font-size: 0.8rem !important;
        border-radius: 10px !important;
    }
    .info-strip-item {
        font-size: 0.82rem;
    }
    .section-header {
        padding: 0.65rem 1rem;
    }
}
</style>
"""
