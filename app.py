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
    PERSONALITY_SECTION,
    NON_USE_REASONS,
    USER_USAGE_QUESTIONS,
    AI_VS_HUMAN_LABELS,
    SCALE_LABELS,
    get_scale_for_section,
    get_scale_size,
)
from utils import (
    generate_participant_id,
    build_question_list,
    get_section_list,
    get_likert_label,
    save_responses_to_csv,
    build_background_css,
    CUSTOM_CSS,
    CSV_PATH,
    _load_bg_image_b64,
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
        "stage": "welcome",           # welcome → screening → demographics → personality → [non_use_reasons | usage_questions] → questionnaire → open_ended → complete
        "participant_id": generate_participant_id(),
        "group": None,                # "User" or "Non-User"
        "demo_idx": 0,
        "personality_idx": 0,         # index within personality assessment
        "usage_q_idx": 0,             # index within USER_USAGE_QUESTIONS
        "current_q_idx": 0,
        "responses": {},              # {question_id: {section, question, response, timestamp}}
        "chat_history": [],           # [{role, content}, …]
        "all_questions": [],          # flat list built after screening
        "section_list": [],           # list of section dicts for progress display
        "submitted": False,
        "needs_typing": False,
        "prev_section": None,         # track section changes for transition messages
        "show_section_interstitial": False,
        "started_at": None,           # ISO timestamp when first question answered
        "completed_at": None,
        "sheets_ok": None,
        "sheets_error": "",
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
    st.markdown(build_background_css("capability"), unsafe_allow_html=True)
    st.write("")
    
    hero_b64 = _load_bg_image_b64("hero_hands.png")
    img_tag = f'<img class="hero-image" src="data:image/png;base64,{hero_b64}" />' if hero_b64 else ''

    # Welcome card
    st.markdown(
        f"""
        <div class="welcome-card">
            {img_tag}
            <div class="welcome-title">Emotional Interaction<br>with AI</div>
            <div class="welcome-subtitle">
                A research study exploring emotional interactions between humans and AI.
            </div>
            <div class="info-strip">
                <div class="info-strip-item">
                    <div class="info-strip-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg></div>
                    <span>About 5-8 minutes. No right or wrong answers.</span>
                </div>
                <div class="info-strip-item">
                    <div class="info-strip-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div>
                    <span>Your responses are completely anonymous.</span>
                </div>
                <div class="info-strip-item">
                    <div class="info-strip-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg></div>
                    <span>For academic research only.</span>
                </div>
                <div class="info-strip-item">
                    <div class="info-strip-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></div>
                    <span>We're interested in your real experiences — how you feel, not just what you think.</span>
                </div>
            </div>
            <div class="consent-box">
                <strong>📋 Before you begin:</strong> There are no right or wrong answers —
                please respond based on your personal experience. Your responses
                are anonymous and will be used solely for academic research.
                By proceeding, you consent to participate.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.markdown(
        '<div style="text-align:center; margin-bottom:1rem; font-size:0.95rem; color:rgba(255,255,255,0.85); font-weight:500;">When you’re ready, tap below to begin.</div>',
        unsafe_allow_html=True,
    )

    # Start button
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button("Start Survey  →", key="btn_start", use_container_width=True):
            st.session_state.stage = "screening"
            st.session_state.needs_typing = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(
        '<div style="text-align:center; margin-top:1.5rem; font-size:0.78rem; color:rgba(255,255,255,0.25);">'
        'Thank you for contributing!</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Screening question (now BEFORE demographics)
# ──────────────────────────────────────────────────────────────────────
def show_screening():
    st.markdown(build_background_css("capability"), unsafe_allow_html=True)

    # Progress bar at top
    st.progress(0.0)
    st.markdown(
        '<div class="progress-label">'
        '<span>Getting started</span>'
        '<span class="progress-percent">0%</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Render chat history
    for msg in st.session_state.chat_history:
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
            time.sleep(0.3)
            placeholder.markdown(f"**{SCREENING_QUESTION}**")
            st.session_state.needs_typing = False
        else:
            st.markdown(f"**{SCREENING_QUESTION}**")

    st.markdown("---")

    st.markdown('<div class="screening-btn">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1.5])
    with col1:
        if st.button("✅  Yes", key="screening_yes", use_container_width=True):
            _handle_screening("Yes")
    with col2:
        if st.button("❌  No", key="screening_no", use_container_width=True):
            _handle_screening("No")
    st.markdown('</div>', unsafe_allow_html=True)


def _handle_screening(answer: str):
    """Process the screening answer and set up the correct questionnaire path."""
    # Record in chat history
    st.session_state.chat_history.append(
        {"role": "assistant", "content": f"**{SCREENING_QUESTION}**"}
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

    # Build full question list: personality (shared) + group-specific Likert sections
    personality_qs = build_question_list(PERSONALITY_SECTION)
    group_qs = build_question_list(sections)
    # Re-index global_index for group questions to come after personality
    for q in group_qs:
        q["global_index"] += len(personality_qs)
    st.session_state.all_questions = personality_qs + group_qs
    st.session_state.section_list = get_section_list(PERSONALITY_SECTION) + get_section_list(sections)
    st.session_state.needs_typing = True
    st.session_state.stage = "demographics"
    st.rerun()


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Demographics
# ──────────────────────────────────────────────────────────────────────
MAX_VISIBLE_HISTORY = 6  # show last N messages to keep UI tidy


def show_demographics():
    idx = st.session_state.demo_idx
    if idx >= len(DEMOGRAPHICS):
        # After demographics, proceed to the main questionnaire
        # (personality is now integrated into all_questions)
        st.session_state.stage = "questionnaire"
        st.session_state.needs_typing = True
        st.session_state.started_at = datetime.now().isoformat()
        st.rerun()

    current = DEMOGRAPHICS[idx]

    st.markdown(build_background_css("capability"), unsafe_allow_html=True)

    # Progress bar
    total_demo = len(DEMOGRAPHICS)
    demo_progress = idx / (total_demo + 1)  # +1 for screening already done
    st.progress(demo_progress * 0.1)  # demographics = first 10% of total
    st.markdown(
        f'<div class="progress-label">'
        f'<span>Demographics · Question {idx + 1} of {total_demo}</span>'
        f'<span class="progress-percent">{int(demo_progress * 10)}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Render chat history
    active_history = st.session_state.chat_history[-MAX_VISIBLE_HISTORY:] if len(st.session_state.chat_history) > MAX_VISIBLE_HISTORY else st.session_state.chat_history
    for msg in active_history:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    with st.chat_message("assistant", avatar="🤖"):
        if idx == 0 and st.session_state.needs_typing:
            st.markdown("👋 Great! Let's start with a few basic questions about you.")
            time.sleep(0.3)

        if st.session_state.needs_typing:
            placeholder = st.empty()
            placeholder.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.3)
            placeholder.markdown(f"**{current['text']}**")
            st.session_state.needs_typing = False
        else:
            if idx == 0:
                st.markdown("👋 Great! Let's start with a few basic questions about you.")
            st.markdown(f"**{current['text']}**")

    st.markdown("---")

    if current.get("options"):
        # Dropdown — auto-advances when user picks a valid option
        selected = st.selectbox(
            current["text"],
            options=["Select an option"] + current["options"],
            key=f"demo_select_{idx}",
            label_visibility="collapsed",
        )

        # Auto-advance on valid selection
        if selected != "Select an option":
            _save_demo_response(current, selected, idx)

        if idx > 0:
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← Back", key=f"demo_back_{idx}", use_container_width=True):
                _undo_demo_response()
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Free-text input (name, age) — uses chat_input for clean mobile UX
        is_age = current["id"] == "demo_age"
        placeholder = "Type your age (e.g. 21)" if is_age else "Type your answer here..."
        user_input = st.chat_input(placeholder)

        if user_input:
            if is_age:
                try:
                    age = int(user_input.strip())
                    if 16 <= age <= 80:
                        _save_demo_response(current, str(age), idx)
                    else:
                        st.warning("Please enter an age between 16 and 80.")
                except ValueError:
                    st.warning("Please enter a valid number for your age.")
            else:
                _save_demo_response(current, user_input, idx)

        if idx > 0:
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← Back", key=f"demo_back_{idx}", use_container_width=True):
                _undo_demo_response()
            st.markdown('</div>', unsafe_allow_html=True)


def _save_demo_response(current, response_text, idx):
    if idx == 0:
        st.session_state.chat_history.append({"role": "assistant", "content": f"👋 Great! Let's start with a few basic questions about you.\n\n**{current['text']}**"})
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


def _undo_demo_response():
    """Go back one step in demographics."""
    if st.session_state.demo_idx > 0:
        st.session_state.demo_idx -= 1
        # Remove last assistant + user message pair from chat history
        if len(st.session_state.chat_history) >= 2:
            st.session_state.chat_history = st.session_state.chat_history[:-2]
        # Remove the response for the previous question
        prev_demo = DEMOGRAPHICS[st.session_state.demo_idx]
        st.session_state.responses.pop(prev_demo["id"], None)
        # Reset selectbox widget state so it doesn't auto-advance on back
        select_key = f"demo_select_{st.session_state.demo_idx}"
        if select_key in st.session_state:
            del st.session_state[select_key]
        st.session_state.needs_typing = False
        st.rerun()


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Questionnaire  (chat-based, one question at a time)
# ──────────────────────────────────────────────────────────────────────
def _get_scale_info(current):
    """Get scale labels and size for the current question's section."""
    scale_key = current.get("scale", "likert")
    labels = SCALE_LABELS.get(scale_key, LIKERT_LABELS)
    size = len(labels)
    return scale_key, labels, size


def _build_scale_ref_html(scale_key, labels, size):
    """Build the scale reference bar and mobile label rows."""
    if scale_key == "ai_vs_human":
        ref = ('<div class="scale-ref">'
               '<span>1 — Trust Human Much More</span>'
               '<span class="scale-ref-center">Equal</span>'
               '<span>7 — Trust AI Much More</span>'
               '</div>')
        mobile = '<div class="likert-labels-row">' + ''.join(
            f'<div class="likert-label-item"><div class="likert-label-num">{v}</div> {labels[v]}</div>'
            for v in range(1, size + 1)
        ) + '</div>'
    else:
        ref = ('<div class="scale-ref">'
               '<span>1 — Strongly Disagree</span>'
               '<span class="scale-ref-center">Neutral</span>'
               '<span>7 — Strongly Agree</span>'
               '</div>')
        mobile = ('<div class="likert-labels-row">'
                  '<div class="likert-label-item"><div class="likert-label-num">1</div> Strongly Disagree</div>'
                  '<div class="likert-label-item"><div class="likert-label-num">2</div> Disagree</div>'
                  '<div class="likert-label-item"><div class="likert-label-num">3</div> Slightly Disagree</div>'
                  '<div class="likert-label-item"><div class="likert-label-num">4</div> Neutral</div>'
                  '<div class="likert-label-item"><div class="likert-label-num">5</div> Slightly Agree</div>'
                  '<div class="likert-label-item"><div class="likert-label-num">6</div> Agree</div>'
                  '<div class="likert-label-item"><div class="likert-label-num">7</div> Strongly Agree</div>'
                  '</div>')
    return ref, mobile


def show_questionnaire():
    all_q = st.session_state.all_questions
    q_idx = st.session_state.current_q_idx

    # ── Check if personality section just ended → route to special stage
    if q_idx > 0 and q_idx < len(all_q):
        prev_q = all_q[q_idx - 1]
        curr_q = all_q[q_idx]
        if prev_q["section_key"] == "personality" and curr_q["section_key"] != "personality":
            # Personality just finished — insert special stage
            if not st.session_state.get("_special_stage_done"):
                if st.session_state.group == "Non-User":
                    st.session_state.stage = "non_use_reasons"
                else:
                    st.session_state.stage = "usage_questions"
                st.session_state.needs_typing = True
                st.rerun()
                return

    # ── Check if all questions are answered ──────────────────────────
    if q_idx >= len(all_q):
        st.session_state.stage = "open_ended"
        st.session_state.needs_typing = True
        st.rerun()
        return

    current = all_q[q_idx]
    total = len(all_q)

    # ── Determine scale type ─────────────────────────────────────────
    scale_key, scale_labels, scale_size = _get_scale_info(current)

    # ── Section-based background ─────────────────────────────────────
    st.markdown(build_background_css(current["background"]), unsafe_allow_html=True)

    # ── Progress bar + label ─────────────────────────────────────────
    progress_frac = q_idx / total
    progress_pct = int(progress_frac * 100)
    st.progress(progress_frac)
    st.markdown(
        f'<div class="progress-label">'
        f'<span>Question {q_idx + 1} of {total} · {current["section_title"]}</span>'
        f'<span class="progress-percent">{progress_pct}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Section transition banner ────────────────────────────────────
    if current["section_key"] != st.session_state.prev_section:
        st.markdown(
            f'<div class="section-header">'
            f'<div class="section-tag">Section</div>'
            f'<h3>📋 {current["section_title"]}</h3>'
            f'</div>',
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
            time.sleep(0.3)
            placeholder.markdown(f"**Q{q_idx + 1}.** {current['text']}")
            st.session_state.needs_typing = False
        else:
            st.markdown(f"**Q{q_idx + 1}.** {current['text']}")

    # ── Scale buttons ────────────────────────────────────────────────
    st.markdown("---")

    # Scale reference (always visible)
    ref_html, mobile_html = _build_scale_ref_html(scale_key, scale_labels, scale_size)
    st.markdown(ref_html, unsafe_allow_html=True)

    cols = st.columns(scale_size, gap="small")
    for i, col in enumerate(cols):
        value = i + 1
        with col:
            if st.button(
                f"{value}",
                key=f"likert_{q_idx}_{value}",
                use_container_width=True,
                help=scale_labels[value],
            ):
                _record_response(current, value, q_idx)

    # Mobile-visible label row
    st.markdown(mobile_html, unsafe_allow_html=True)

    # Tap hint
    st.markdown(
        '<div class="tap-hint">'
        '<span class="tap-hint-icon">💡</span>'
        'Tap a number to see the full label'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Back button ──────────────────────────────────────────────────
    if q_idx > 0:
        st.write("")
        col_back, col_space = st.columns([1, 3])
        with col_back:
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← Back", key=f"q_back_{q_idx}", use_container_width=True):
                _undo_response()
            st.markdown('</div>', unsafe_allow_html=True)




def _record_response(current: dict, value: int, q_idx: int):
    """Save the participant's response and advance to the next question."""
    scale_key = current.get("scale", "likert")
    labels = SCALE_LABELS.get(scale_key, LIKERT_LABELS)
    label = labels.get(value, str(value))

    # Append to persistent chat history
    st.session_state.chat_history.append(
        {"role": "assistant", "content": f"**Q{q_idx + 1}.** {current['text']}"}
    )
    st.session_state.chat_history.append(
        {"role": "user", "content": f"**{value}** — {label}"}
    )

    # Store response data
    response_data = {
        "section": current["section_title"],
        "question": current["text"],
        "response": value,
        "timestamp": datetime.now().isoformat(),
    }
    st.session_state.responses[current["id"]] = response_data

    # Advance
    st.session_state.current_q_idx += 1
    st.session_state.needs_typing = True
    st.rerun()


def _undo_response():
    """Go back one question in the questionnaire."""
    if st.session_state.current_q_idx > 0:
        st.session_state.current_q_idx -= 1
        # Remove last assistant + user message pair from chat history
        if len(st.session_state.chat_history) >= 2:
            st.session_state.chat_history = st.session_state.chat_history[:-2]
        # Remove the response
        prev_q = st.session_state.all_questions[st.session_state.current_q_idx]
        st.session_state.responses.pop(prev_q["id"], None)
        st.session_state.needs_typing = False
        st.session_state.show_section_interstitial = False

        # Update prev_section to match the question we're going back to
        if st.session_state.current_q_idx > 0:
            prev_prev_q = st.session_state.all_questions[st.session_state.current_q_idx - 1]
            st.session_state.prev_section = prev_prev_q["section_key"]
        else:
            st.session_state.prev_section = None

        st.rerun()


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Non-Use Reasons (multi-select — Non-User only)
# ──────────────────────────────────────────────────────────────────────
def show_non_use_reasons():
    st.markdown(build_background_css("concerns"), unsafe_allow_html=True)

    total = len(st.session_state.all_questions)
    personality_count = len(PERSONALITY_SECTION["personality"]["questions"])
    progress_frac = personality_count / total
    st.progress(progress_frac)
    st.markdown(
        f'<div class="progress-label">'
        f'<span>{NON_USE_REASONS["section"]}</span>'
        f'<span class="progress-percent">{int(progress_frac * 100)}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-header">'
        '<div class="section-tag">Section</div>'
        f'<h3>📋 {NON_USE_REASONS["section"]}</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(f"**{NON_USE_REASONS['text']}**")

    st.markdown("---")

    selected = []
    for i, opt in enumerate(NON_USE_REASONS["options"]):
        if st.checkbox(opt, key=f"non_use_{i}"):
            selected.append(opt)

    other_text = st.text_input(
        "Other reason (optional):",
        key="non_use_other",
        placeholder="Type your reason here...",
    )

    st.write("")
    col_l, col_r = st.columns([1, 1])
    with col_r:
        st.markdown('<div class="next-btn">', unsafe_allow_html=True)
        if st.button("Next →", key="non_use_next", use_container_width=True):
            if not selected and not other_text.strip():
                st.warning("Please select at least one reason to continue.")
            else:
                if other_text.strip():
                    selected.append(f"Other: {other_text.strip()}")
                response_text = "; ".join(selected)
                st.session_state.responses[NON_USE_REASONS["id"]] = {
                    "section": NON_USE_REASONS["section"],
                    "question": NON_USE_REASONS["text"],
                    "response": response_text,
                    "timestamp": datetime.now().isoformat(),
                }
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": f"**{NON_USE_REASONS['text']}**"}
                )
                st.session_state.chat_history.append(
                    {"role": "user", "content": response_text}
                )
                st.session_state._special_stage_done = True
                st.session_state.stage = "questionnaire"
                st.session_state.needs_typing = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Usage Questions (frequency & duration — User only)
# ──────────────────────────────────────────────────────────────────────
def show_usage_questions():
    idx = st.session_state.usage_q_idx

    if idx >= len(USER_USAGE_QUESTIONS):
        st.session_state._special_stage_done = True
        st.session_state.stage = "questionnaire"
        st.session_state.needs_typing = True
        st.rerun()
        return

    current = USER_USAGE_QUESTIONS[idx]
    st.markdown(build_background_css("usage"), unsafe_allow_html=True)

    total = len(st.session_state.all_questions)
    personality_count = len(PERSONALITY_SECTION["personality"]["questions"])
    progress_frac = personality_count / total
    st.progress(progress_frac)
    st.markdown(
        f'<div class="progress-label">'
        f'<span>{current["section"]} · Question {idx + 1} of {len(USER_USAGE_QUESTIONS)}</span>'
        f'<span class="progress-percent">{int(progress_frac * 100)}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if idx == 0:
        st.markdown(
            '<div class="section-header">'
            '<div class="section-tag">Section</div>'
            '<h3>📋 AI Usage Patterns</h3>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Chat history
    history = st.session_state.chat_history
    visible = history[-MAX_VISIBLE_HISTORY:] if len(history) > MAX_VISIBLE_HISTORY else history
    for msg in visible:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(f"**{current['text']}**")

    st.markdown("---")

    selected = st.selectbox(
        current["text"],
        options=["Select an option"] + current["options"],
        key=f"usage_select_{idx}",
        label_visibility="collapsed",
    )

    col_back, col_space, col_next = st.columns([1, 1, 1])
    if idx > 0:
        with col_back:
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← Back", key=f"usage_back_{idx}", use_container_width=True):
                st.session_state.usage_q_idx -= 1
                if len(st.session_state.chat_history) >= 2:
                    st.session_state.chat_history = st.session_state.chat_history[:-2]
                prev_q = USER_USAGE_QUESTIONS[st.session_state.usage_q_idx]
                st.session_state.responses.pop(prev_q["id"], None)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    with col_next:
        st.markdown('<div class="next-btn">', unsafe_allow_html=True)
        if st.button("Next →", key=f"usage_next_{idx}", use_container_width=True):
            if selected != "Select an option":
                st.session_state.responses[current["id"]] = {
                    "section": current["section"],
                    "question": current["text"],
                    "response": selected,
                    "timestamp": datetime.now().isoformat(),
                }
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": f"**{current['text']}**"}
                )
                st.session_state.chat_history.append(
                    {"role": "user", "content": selected}
                )
                st.session_state.usage_q_idx += 1
                st.session_state.needs_typing = True
                st.rerun()
            else:
                st.warning("Please select an option to continue.")
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# SCREEN: Optional open-ended question
# ──────────────────────────────────────────────────────────────────────
def show_open_ended():
    st.markdown(build_background_css("trust"), unsafe_allow_html=True)

    total = len(st.session_state.all_questions)
    st.progress(1.0)
    st.markdown(
        '<div class="progress-label">'
        '<span>Almost done!</span>'
        '<span class="progress-percent">100%</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.chat_message("assistant", avatar="🤖"):
        if st.session_state.needs_typing:
            placeholder = st.empty()
            placeholder.markdown(
                '<div class="typing-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.3)
            placeholder.markdown(
                "**One last thing!** Would you like to share anything about your "
                "experience talking to AI emotionally? *(This is completely optional)*"
            )
            st.session_state.needs_typing = False
        else:
            st.markdown(
                "**One last thing!** Would you like to share anything about your "
                "experience talking to AI emotionally? *(This is completely optional)*"
            )

    st.markdown("---")

    open_text = st.text_area(
        "Your thoughts (optional)",
        placeholder="Share your thoughts here... or skip to finish.",
        key="open_ended_text",
        height=120,
        label_visibility="collapsed",
    )

    col_skip, col_space, col_submit = st.columns([1, 1, 1])
    with col_skip:
        st.markdown('<div class="skip-btn">', unsafe_allow_html=True)
        if st.button("Skip →", key="skip_open_ended", use_container_width=True):
            _finalise_and_save()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_submit:
        st.markdown('<div class="next-btn">', unsafe_allow_html=True)
        if st.button("Submit →", key="submit_open_ended", use_container_width=True):
            if open_text and open_text.strip():
                st.session_state.responses["open_ended_Q1"] = {
                    "section": "Open-Ended",
                    "question": "Would you like to share anything about your experience talking to AI emotionally?",
                    "response": open_text.strip(),
                    "timestamp": datetime.now().isoformat(),
                }
            _finalise_and_save()
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# Finalise and save
# ──────────────────────────────────────────────────────────────────────
def _finalise_and_save():
    """Persist responses to CSV and transition to the completion screen."""
    if not st.session_state.submitted:
        st.session_state.completed_at = datetime.now().isoformat()

        # Calculate duration
        duration = ""
        if st.session_state.started_at:
            try:
                start = datetime.fromisoformat(st.session_state.started_at)
                end = datetime.fromisoformat(st.session_state.completed_at)
                duration = str(int((end - start).total_seconds()))
            except Exception:
                duration = ""

        sheets_ok, error_msg = save_responses_to_csv(
            participant_id=st.session_state.participant_id,
            group=st.session_state.group,
            responses=st.session_state.responses,
            started_at=st.session_state.started_at or "",
            completed_at=st.session_state.completed_at,
            duration_seconds=duration,
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
    sheets_ok = st.session_state.get("sheets_ok", True)

    # Determine status-dependent styling
    if sheets_ok:
        card_class = "success"
        check_icon = "✅"
        title_text = "Thank You!"
        status_text = "Your responses have been recorded successfully."
        badge_icon = "🗂️"
        badge_text = f"Participant ID: <strong>{pid}</strong> · Data saved securely"
    else:
        card_class = "warning"
        check_icon = "⚠️"
        title_text = "Survey Completed"
        status_text = "Your responses have been saved locally. There was an issue with cloud storage."
        badge_icon = "📁"
        badge_text = f"Participant ID: <strong>{pid}</strong> · Saved to local backup"

    st.markdown(
        f"""
        <div class="completion-card {card_class}">
            <div class="completion-check {card_class}">{check_icon}</div>
            <div class="completion-title {card_class}">{title_text}</div>
            <div class="completion-text">
                {status_text}<br>
                You answered all <strong>{total}</strong> questions as a
                <strong>{group}</strong> participant.
            </div>
            <div class="saved-badge {card_class}">
                {badge_icon} &nbsp;{badge_text}
            </div>
            <div style="margin-top:1.5rem; font-size:0.82rem; color:rgba(255,255,255,0.4); line-height:1.6;">
                Your anonymous responses will contribute to academic research on<br>
                emotional interaction with artificial intelligence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show detailed error if sheets failed
    if not sheets_ok:
        st.warning(
            f"**Storage Notice:** Cloud save encountered an issue. "
            f"Your responses are safely stored in the local backup and will be synced later.\n\n"
            f"*Technical detail: {st.session_state.get('sheets_error', 'Unknown error')}*",
            icon="⚠️"
        )

    # Privacy reassurance
    st.markdown(
        '<div style="text-align:center; margin:1rem 0;">'
        '<div style="display:inline-flex; align-items:center; gap:0.5rem; '
        'padding:0.5rem 1rem; background:rgba(124,58,237,0.06); border-radius:10px; '
        'border:1px solid rgba(124,58,237,0.1); font-size:0.82rem; color:rgba(255,255,255,0.45);">'
        '🔒 Your data is safe and confidential'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Download + Finish
    st.markdown("")
    _offer_download()

    st.write("")
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center; padding:0.75rem; '
            'background:linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); '
            'border-radius:14px; color:white; font-weight:600; font-size:1rem; '
            'cursor:default;">Finish</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="text-align:center; margin-top:1rem; font-size:0.78rem; '
        'color:rgba(255,255,255,0.25);">We truly appreciate your time and valuable contribution!</div>',
        unsafe_allow_html=True,
    )


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
            get_likert_label(data["response"]) if isinstance(data["response"], int) else "",
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
    elif stage == "screening":
        show_screening()
    elif stage == "demographics":
        show_demographics()
    elif stage == "non_use_reasons":
        show_non_use_reasons()
    elif stage == "usage_questions":
        show_usage_questions()
    elif stage == "questionnaire":
        show_questionnaire()
    elif stage == "open_ended":
        show_open_ended()
    elif stage == "complete":
        show_completion()


if __name__ == "__main__":
    main()
