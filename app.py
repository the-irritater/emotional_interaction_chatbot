"""
Emotional Interaction with AI — Chatbot-Based Questionnaire System
==================================================================
A Streamlit application that collects research questionnaire responses
through an interactive chatbot-style interface with section-based
dynamic backgrounds, typing animations, and structured data export.

Run:  streamlit run app.py
"""

import streamlit as st
import time
from datetime import datetime

from questions import (
    SCREENING_QUESTION,
    NON_USER_SECTIONS,
    USER_SECTIONS,
    LIKERT_LABELS,
    DEMOGRAPHICS,
)
from utils import (
    generate_participant_id,
    build_question_list,
    get_likert_label,
    save_responses_to_csv,
    build_background_css,
    CUSTOM_CSS,
    CSV_PATH,
)


# ──────────────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Emotional Interaction with AI — Research Questionnaire",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ──────────────────────────────────────────────────────────────────────
# Session state initialisation
# ──────────────────────────────────────────────────────────────────────
def init_session_state():
    """Set default values for every session-state key on first load."""
    defaults = {
        "stage": "welcome",           # welcome → demographics → screening → questionnaire → complete
        "participant_id": generate_participant_id(),
        "group": None,                # "User" or "Non-User"
        "demo_idx": 0,
        "current_q_idx": 0,
        "responses": {},              # {question_id: {section, question, response, timestamp}}
        "chat_history": [],           # [{role, content}, …]
        "all_questions": [],          # flat list built after screening
        "submitted": False,
        "needs_typing": False,
        "prev_section": None,         # track section changes for transition messages
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ──────────────────────────────────────────────────────────────────────
# Inject global CSS
# ──────────────────────────────────────────────────────────────────────
def inject_styles():
    # Remove empty lines to prevent Streamlit from breaking the <style> block
    clean_css = "\n".join(line for line in CUSTOM_CSS.splitlines() if line.strip())
    st.markdown(clean_css, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Welcome
# ──────────────────────────────────────────────────────────────────────
def show_welcome():
    import os
    from utils import ASSETS_DIR

    # Set welcome background
    st.markdown(build_background_css("capability"), unsafe_allow_html=True)
    st.write("")
    st.write("")

    # Title
    st.title("Emotional Interaction with AI")
    st.subheader("Chatbot-Based Research Questionnaire")
    st.write("---")

    # Study description
    st.write(
        "This study explores how people perceive **emotional interactions "
        "with Artificial Intelligence** systems such as ChatGPT, Replika, Alexa, and Gemini.\n\n"
        "You will be guided through a series of questions about your "
        "**beliefs, experiences, and trust** regarding AI's role in emotional conversations. "
        "The questionnaire takes approximately **5–8 minutes** to complete."
    )
    


    # Consent / Privacy notice
    st.info(
        "🔒 **Privacy Notice:**\n\n"
        "Your responses are completely anonymous and will be used solely for "
        "academic research purposes. No personally identifiable information "
        "is collected. By proceeding, you consent to participate in this study."
    )

    st.write("")

    # Start button
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        if st.button("Begin Survey  →", key="btn_start", use_container_width=True):
            st.session_state.stage = "demographics"
            st.session_state.needs_typing = True
            st.rerun()


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Demographics
# ──────────────────────────────────────────────────────────────────────
def show_demographics():
    idx = st.session_state.demo_idx
    if idx >= len(DEMOGRAPHICS):
        st.session_state.stage = "screening"
        st.session_state.needs_typing = True
        st.rerun()

    current = DEMOGRAPHICS[idx]
    
    st.markdown(build_background_css("capability"), unsafe_allow_html=True)
    
    # Render chat history
    active_history = st.session_state.chat_history[-MAX_VISIBLE_HISTORY:] if len(st.session_state.chat_history) > MAX_VISIBLE_HISTORY else st.session_state.chat_history
    for msg in active_history:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
    with st.chat_message("assistant", avatar="🤖"):
        if idx == 0 and st.session_state.needs_typing:
            st.markdown("👋 Welcome! Let's get some basic information first.")
            time.sleep(0.5)

        if st.session_state.needs_typing:
            placeholder = st.empty()
            placeholder.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.5)
            placeholder.markdown(f"**{current['text']}**")
            st.session_state.needs_typing = False
        else:
            if idx == 0:
                st.markdown("👋 Welcome! Let's get some basic information first.")
            st.markdown(f"**{current['text']}**")
        
    st.markdown("---")
    
    if current.get("options"):
        cols = st.columns(len(current["options"]), gap="small")
        for i, col in enumerate(cols):
            with col:
                opt = current["options"][i]
                if st.button(opt, key=f"demo_{idx}_{i}", use_container_width=True):
                    _save_demo_response(current, opt, idx)
    else:
        user_input = st.chat_input("Type your answer here...")
        if user_input:
            _save_demo_response(current, user_input, idx)

def _save_demo_response(current, response_text, idx):
    if idx == 0:
        st.session_state.chat_history.append({"role": "assistant", "content": f"👋 Welcome! Let's get some basic information first.\n\n**{current['text']}**"})
    else:
        st.session_state.chat_history.append({"role": "assistant", "content": f"**{current['text']}**"})
    st.session_state.chat_history.append({"role": "user", "content": response_text})
    st.session_state.responses[current["id"]] = {
        "section": "Demographics",
        "question": current["text"],
        "response": response_text,
        "timestamp": datetime.now().isoformat(),
    }
    st.session_state.demo_idx += 1
    st.session_state.needs_typing = True
    st.rerun()

# ──────────────────────────────────────────────────────────────────────
# SCREEN: Screening question
# ──────────────────────────────────────────────────────────────────────
def show_screening():
    st.markdown(build_background_css("capability"), unsafe_allow_html=True)
    
    # Render chat history
    active_history = st.session_state.chat_history[-MAX_VISIBLE_HISTORY:] if len(st.session_state.chat_history) > MAX_VISIBLE_HISTORY else st.session_state.chat_history
    for msg in active_history:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    with st.chat_message("assistant", avatar="🤖"):
        if st.session_state.needs_typing:
            placeholder = st.empty()
            placeholder.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.5)
            placeholder.markdown(f"**{SCREENING_QUESTION}**")
            st.session_state.needs_typing = False
        else:
            st.markdown(f"**{SCREENING_QUESTION}**")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1.5])
    with col1:
        if st.button("✅  Yes", key="screening_yes", use_container_width=True):
            _handle_screening("Yes")
    with col2:
        if st.button("❌  No", key="screening_no", use_container_width=True):
            _handle_screening("No")


def _handle_screening(answer: str):
    """Process the screening answer and set up the correct questionnaire path."""
    # Record in chat history
    st.session_state.chat_history.append(
        {"role": "assistant", "content": SCREENING_QUESTION}
    )
    st.session_state.chat_history.append(
        {"role": "user", "content": answer}
    )

    if answer == "Yes":
        st.session_state.group = "User"
        sections = USER_SECTIONS
    else:
        st.session_state.group = "Non-User"
        sections = NON_USER_SECTIONS

    st.session_state.all_questions = build_question_list(sections)
    st.session_state.current_q_idx = 0
    st.session_state.needs_typing = True
    st.session_state.stage = "questionnaire"
    st.rerun()


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Questionnaire  (chat-based, one question at a time)
# ──────────────────────────────────────────────────────────────────────
MAX_VISIBLE_HISTORY = 6  # show last N messages to keep UI tidy


def show_questionnaire():
    all_q = st.session_state.all_questions
    q_idx = st.session_state.current_q_idx

    # ── Check if all questions are answered ──────────────────────────
    if q_idx >= len(all_q):
        _finalise_and_save()
        return

    current = all_q[q_idx]
    total = len(all_q)

    # ── Section-based background ─────────────────────────────────────
    st.markdown(build_background_css(current["background"]), unsafe_allow_html=True)

    # ── Progress bar + label ─────────────────────────────────────────
    progress_frac = q_idx / total
    st.progress(progress_frac)
    st.markdown(
        f'<div class="progress-label">Question {q_idx + 1} of {total} &nbsp;·&nbsp; {current["section_title"]}</div>',
        unsafe_allow_html=True,
    )

    # ── Section transition banner ────────────────────────────────────
    if current["section_key"] != st.session_state.prev_section:
        st.markdown(
            f'<div class="section-header"><h3>📋 {current["section_title"]}</h3></div>',
            unsafe_allow_html=True,
        )
        st.session_state.prev_section = current["section_key"]

    # ── Render recent chat history ───────────────────────────────────
    history = st.session_state.chat_history
    visible = history[-MAX_VISIBLE_HISTORY:] if len(history) > MAX_VISIBLE_HISTORY else history

    for msg in visible:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # ── Current question (with optional typing animation) ────────────
    with st.chat_message("assistant", avatar="🤖"):
        if st.session_state.needs_typing:
            placeholder = st.empty()
            placeholder.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.7)
            placeholder.markdown(f"**Q{q_idx + 1}.** {current['text']}")
            st.session_state.needs_typing = False
        else:
            st.markdown(f"**Q{q_idx + 1}.** {current['text']}")

    # ── Likert scale ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<div class="scale-ref">'
        "<span>1 — Strongly Disagree</span>"
        "<span>7 — Strongly Agree</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(7, gap="small")
    short_labels = ["SD", "D", "SlD", "N", "SlA", "A", "SA"]

    for i, col in enumerate(cols):
        value = i + 1
        with col:
            btn_label = f"{value}"
            if st.button(
                btn_label,
                key=f"likert_{q_idx}_{value}",
                use_container_width=True,
                help=LIKERT_LABELS[value],
            ):
                _record_response(current, value, q_idx)

    # Tooltip legend
    st.markdown(
        '<div style="text-align:center; font-size:0.7rem; color:rgba(255,255,255,0.3); margin-top:6px;">'
        "Hover over a button to see the full label"
        "</div>",
        unsafe_allow_html=True,
    )


def _record_response(current: dict, value: int, q_idx: int):
    """Save the participant's response and advance to the next question."""
    label = get_likert_label(value)

    # Append to persistent chat history
    st.session_state.chat_history.append(
        {"role": "assistant", "content": f"**Q{q_idx + 1}.** {current['text']}"}
    )
    st.session_state.chat_history.append(
        {"role": "user", "content": f"**{value}** — {label}"}
    )

    # Store response data
    st.session_state.responses[current["id"]] = {
        "section": current["section_title"],
        "question": current["text"],
        "response": value,
        "timestamp": datetime.now().isoformat(),
    }

    # Advance
    st.session_state.current_q_idx += 1
    st.session_state.needs_typing = True
    st.rerun()


def _finalise_and_save():
    """Persist responses to CSV and transition to the completion screen."""
    if not st.session_state.submitted:
        sheets_ok, error_msg = save_responses_to_csv(
            participant_id=st.session_state.participant_id,
            group=st.session_state.group,
            responses=st.session_state.responses,
        )
        st.session_state.submitted = True
        st.session_state.sheets_ok = sheets_ok
        st.session_state.sheets_error = error_msg

    st.session_state.stage = "complete"
    st.rerun()


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Completion / Thank-you
# ──────────────────────────────────────────────────────────────────────
def show_completion():
    # Reset background to a calm finish gradient
    st.markdown(
        build_background_css("trust"),
        unsafe_allow_html=True,
    )

    total = len(st.session_state.all_questions)
    pid = st.session_state.participant_id
    group = st.session_state.group

    st.markdown(
        f"""
        <div class="completion-card">
            <div class="completion-check">✅</div>
            <div class="completion-title">Thank You!</div>
            <div class="completion-text">
                Your responses have been recorded successfully.<br>
                You answered all <strong>{total}</strong> questions as a
                <strong>{group}</strong> participant.
            </div>
            <div class="saved-badge">
                🗂️ &nbsp;Participant ID: <strong>{pid}</strong> &nbsp;·&nbsp; Data saved securely
            </div>
            <div style="margin-top:1.5rem; font-size:0.82rem; color:rgba(255,255,255,0.4); line-height:1.6;">
                Your anonymous responses will contribute to academic research on<br>
                emotional interaction with artificial intelligence. You may now close this page.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display Google Sheets Error if it failed
    if st.session_state.get("sheets_ok") is False:
        st.error(
            f"**Warning:** Could not save to Google Sheets. "
            f"Error: {st.session_state.get('sheets_error')}\n\n"
            f"Responses were saved to the local server, but you are not connected to Google Sheets.",
            icon="🚨"
        )

    # Optional CSV download
    st.markdown("")
    _offer_download()


def _offer_download():
    """Offer the participant a download of their own responses (optional)."""
    import csv
    import io

    responses = st.session_state.responses
    if not responses:
        return

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Question ID", "Section", "Question", "Response", "Label"])
    for q_id, data in responses.items():
        writer.writerow([
            q_id,
            data["section"],
            data["question"],
            data["response"],
            get_likert_label(data["response"]),
        ])

    col_l, col_c, col_r = st.columns([1.2, 1, 1.2])
    with col_c:
        st.download_button(
            label="📥  Download My Responses",
            data=buf.getvalue(),
            file_name=f"responses_{st.session_state.participant_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def main():
    init_session_state()
    inject_styles()

    stage = st.session_state.stage

    if stage == "welcome":
        show_welcome()
    elif stage == "demographics":
        show_demographics()
    elif stage == "screening":
        show_screening()
    elif stage == "questionnaire":
        show_questionnaire()
    elif stage == "complete":
        show_completion()


if __name__ == "__main__":
    main()
