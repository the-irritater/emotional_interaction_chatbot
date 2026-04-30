"""
Questionnaire Data Module
=========================
Contains all questionnaire items for both User and Non-User groups.
Questions are stored in ordered dictionaries to maintain correct sequencing.
All question text is preserved verbatim from the validated research instrument.

Response Scales:
    Likert (7-point, default — used for all sections including Personality):
        1 = Strongly Disagree
        2 = Disagree
        3 = Slightly Disagree
        4 = Neutral
        5 = Slightly Agree
        6 = Agree
        7 = Strongly Agree

    AI vs Human Trust (7-point):
        1 = Trust Human Much More
        2 = Trust Human More
        3 = Trust Human Slightly More
        4 = Trust Both Equally
        5 = Trust AI Slightly More
        6 = Trust AI More
        7 = Trust AI Much More
"""

from collections import OrderedDict


# ---------------------------------------------------------------------------
# Screening
# ---------------------------------------------------------------------------
SCREENING_QUESTION = (
    "Have you ever used AI for emotional interaction or support?"
)

# ---------------------------------------------------------------------------
# Demographics
# ---------------------------------------------------------------------------
DEPARTMENT_OPTIONS = [
    "Statistics",
    "Physics",
    "Chemistry",
    "Psychology",
    "Maths",
    "Library Science",
    "Economics",
    "Bio-Technology",
    "Computer Science",
    "Management",
    "Law",
    "Life Science",
    "Geography",
    "International Studies",
    "Sanskrit",
    "Other",
]

DEMOGRAPHICS = [
    {
        "id": "demo_name",
        "text": "What is your name or nickname?",
        # free-text input (no "options" key)
    },
    {
        "id": "demo_age",
        "text": "What is your age?",
        "input_type": "number",
        "min_value": 16,
        "max_value": 80,
        "placeholder": "Enter your age (e.g. 21)",
    },
    {
        "id": "demo_gender",
        "text": "What is your gender?",
        "options": ["Male", "Female", "Non-binary", "Prefer not to say"],
    },
    {
        "id": "demo_dept",
        "text": "Which department do you belong to?",
        "options": DEPARTMENT_OPTIONS,
    },
]

# (Personality uses the same 7-point Likert scale as other sections)

# ---------------------------------------------------------------------------
# Likert scale anchors (7-point, default for most sections)
# ---------------------------------------------------------------------------
LIKERT_LABELS = {
    1: "Strongly Disagree",
    2: "Disagree",
    3: "Slightly Disagree",
    4: "Neutral",
    5: "Slightly Agree",
    6: "Agree",
    7: "Strongly Agree",
}

# ---------------------------------------------------------------------------
# AI vs Human Trust scale anchors (7-point)
# ---------------------------------------------------------------------------
AI_VS_HUMAN_LABELS = {
    1: "Trust Human Much More",
    2: "Trust Human More",
    3: "Trust Human Slightly More",
    4: "Trust Both Equally",
    5: "Trust AI Slightly More",
    6: "Trust AI More",
    7: "Trust AI Much More",
}

# ---------------------------------------------------------------------------
# Section background theme mapping
# Each key maps to a CSS gradient defined in the app
# ---------------------------------------------------------------------------
SECTION_BACKGROUNDS = {
    "capability": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    "authenticity": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
    "openness": "linear-gradient(135deg, #0a1628 0%, #134e5e 50%, #1a4040 100%)",
    "concerns": "linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a2e 100%)",
    "trust": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)",
    "motivation": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
    "empathy": "linear-gradient(135deg, #0a1628 0%, #1a3a4a 50%, #1a4040 100%)",
    "personality": "linear-gradient(135deg, #1a0a2e 0%, #2d1b69 50%, #1a1a2e 100%)",
    "usage": "linear-gradient(135deg, #0a192f 0%, #1a365d 50%, #0f3460 100%)",
    "comparison": "linear-gradient(135deg, #0f0c29 0%, #1a2a3e 50%, #24243e 100%)",
    "future": "linear-gradient(135deg, #0a1628 0%, #1a4040 50%, #134e5e 100%)",
}


# ---------------------------------------------------------------------------
# Personality Assessment (Section 1) — shared by BOTH User & Non-User
# Big Five Extraversion subscale (BFI-10 style), 5-point accuracy scale
# ---------------------------------------------------------------------------
PERSONALITY_SECTION = OrderedDict([
    ("personality", {
        "title": "Personality Assessment",
        "subtitle": "Please rate the following statements based on how accurately they describe you.",
        "background": "personality",
        "scale": "likert",  # 7-point Likert, same as other sections
        "questions": [
            "I see myself as someone who is talkative.",
            "I see myself as someone who is reserved.",                                      # Reversed
            "I see myself as someone who is full of energy.",
            "I see myself as someone who generates a lot of enthusiasm.",
            "I see myself as someone who tends to stay quiet.",                               # Reversed
            "I see myself as someone who is confident and expresses opinion clearly.",
            "I see myself as someone who is sometimes shy, inhibited.",                       # Reversed
            "I see myself as someone who is outgoing, sociable.",
        ],
    }),
])


# ---------------------------------------------------------------------------
# Non-User — Reasons for NOT using AI (multi-select, Section 2)
# ---------------------------------------------------------------------------
NON_USE_REASONS = {
    "id": "non_use_reasons",
    "section": "Perceptions of Non-Users",
    "text": "What are the main reasons you have NOT used an AI chatbot for emotional support? (Select all that apply)",
    "input_type": "multiselect",
    "options": [
        "I don't believe AI can truly understand emotions",
        "It feels unnatural or strange to open up to a machine",
        "I worry about my private feelings being stored or misused",
        "I have enough human support and don't feel the need",
        "I don't trust the advice or responses it would give",
        "It feels like a replacement for real human connection, which I find uncomfortable",
        "I am concerned I could become dependent on it",
        "I simply haven't thought about it as an option before",
    ],
    "allow_other": True,  # show a free-text "Other" field
}


# ---------------------------------------------------------------------------
# Non-User Questionnaire
# ---------------------------------------------------------------------------
NON_USER_SECTIONS = OrderedDict([
    # Section 3 — Perceived Authenticity of AI Emotional Responses
    ("perceived_authenticity", {
        "title": "Perceived Authenticity of AI Emotional Responses",
        "background": "authenticity",
        "scale": "likert",
        "questions": [
            "In my opinion, emotional responses generated by AI would likely feel artificial.",
            "I believe emotional support from AI cannot fully replace genuine human care.",
            "I think conversations with AI would probably feel less authentic than conversations with people.",
            "I believe AI may appear empathetic but its responses are ultimately programmed.",
        ],
    }),
    # Section 4 — Concerns and Skepticism About Emotional AI
    ("concerns_skepticism", {
        "title": "Concerns and Skepticism About Emotional AI",
        "background": "concerns",
        "scale": "likert",
        "questions": [
            "I would probably worry about privacy if someone shared emotions with AI.",
            "I believe people might become too emotionally dependent on AI.",
            "Emotional conversations with AI might reduce real human interactions.",
            "I would likely hesitate to trust emotional advice from AI.",
        ],
    }),
    # Section 5 — Openness Toward Emotional AI Interaction
    ("openness", {
        "title": "Openness Toward Emotional AI Interaction",
        "background": "openness",
        "scale": "likert",
        "questions": [
            "I might consider talking to AI about personal feelings in the future.",
            "I think AI could become a useful emotional support tool for some people.",
            "I am curious about how AI systems handle emotional conversations.",
            "I might feel comfortable sharing minor concerns with AI.",
            "Over the next 10 years, AI is likely to become a common and widely accepted source of emotional support.",
            "I am comfortable with my close ones relying on AI for emotional support.",
        ],
    }),
])


# ---------------------------------------------------------------------------
# User — AI Usage Frequency & Duration (special input questions)
# These are handled BEFORE the Likert sections in app flow
# ---------------------------------------------------------------------------
USER_USAGE_QUESTIONS = [
    {
        "id": "usage_frequency",
        "section": "AI Usage Frequency",
        "text": (
            "How often do you turn to AI for emotional support?"
        ),
        "input_type": "select",
        "options": [
            "Rarely (1–3 times/month)",
            "Occasionally (4–8 times/month)",
            "Frequently (9–15 times/month)",
            "Very frequently (16+ times/month)",
        ],
    },
    {
        "id": "usage_duration",
        "section": "Duration of Emotional AI Interactions",
        "text": (
            "When you do use AI emotionally, conversations typically last:"
        ),
        "input_type": "select",
        "options": [
            "Less than 5 minutes",
            "5–15 minutes",
            "16–30 minutes",
            "More than 30 minutes",
        ],
    },
]


# ---------------------------------------------------------------------------
# User Questionnaire  (Likert sections)
# ---------------------------------------------------------------------------
USER_SECTIONS = OrderedDict([
    # Motivation to Use AI for Emotional Interaction (Q3–Q10)
    ("motivation", {
        "title": "Motivation to Use AI for Emotional Interaction",
        "subtitle": "Rate each statement based on your personal reasons for using AI for emotional support.",
        "background": "motivation",
        "scale": "likert",
        "questions": [
            "I use AI because it is available 24×7 whenever I need support.",
            "I find it easier to express my thoughts and emotions to AI.",
            "I feel comfortable sharing personal things with AI.",
            "AI helps me think more clearly about my problems.",
            "I prefer AI when I feel embarrassed to talk to someone.",
            "Talking to AI helps me feel better when I am stressed.",
            "I use AI because it does not judge me.",
            "I use AI because I am curious about how it responds.",
        ],
    }),

    # Perceived Empathy of AI (Q11–Q16)
    ("perceived_empathy", {
        "title": "Perceived Empathy of AI",
        "subtitle": "Think about a typical or recent interaction with AI and rate how it responded to your emotions.",
        "background": "empathy",
        "scale": "likert",
        "questions": [
            "The AI considered my emotional state during the interaction.",
            "The AI responded to my feelings in an appropriate way.",
            "The AI reacted sympathetically when I expressed concerns or problems.",
            "The AI showed interest in my emotional situation.",
            "The AI understood my goals and what I wanted to accomplish.",
            "The AI understood my needs during the interaction.",
        ],
    }),

    # Perceived Authenticity in Emotional AI Interaction (Q17–Q24)
    ("perceived_authenticity", {
        "title": "Perceived Authenticity in Emotional AI Interaction",
        "subtitle": "Rate how natural and genuine the AI felt during emotional interactions.",
        "background": "authenticity",
        "scale": "likert",
        "questions": [
            "The AI's responses fit naturally within the flow of conversation.",
            "The AI maintains a consistent tone during emotional interactions.",
            "The AI expresses emotions in a way that feels human-like.",
            "Interacting with the AI feels similar to interacting with a person.",
            "The AI's emotional responses feel genuine rather than artificial.",
            "The AI clearly explains or reflects how it responds during emotional interactions.",
            "The AI adapts its responses based on my inputs and past interactions.",
            "The AI improves its responses over time as I continue interacting with it.",
        ],
    }),

    # Trust in AI (Q25–Q32)
    ("trust_in_ai", {
        "title": "Trust in AI",
        "background": "trust",
        "scale": "likert",
        "questions": [
            "I understand how the AI system works, how it behaves, and what I can expect from it.",
            "The AI system consistently provides reliable results under similar conditions over time.",
            "When I need help, the AI system responds effectively and in a timely manner.",
            "I find that the AI system suits my preferences and needs.",
            "I like using the AI system and would prefer to continue using it.",
            "I feel in control when using the AI system and its features.",
            "I tend to rely on the AI system's results, even when I am uncertain about them.",
            "I remain confident in the AI system's ability to provide the best results, even when I have doubts.",
        ],
    }),

    # AI vs Human Comparison — Likert items (Q33–Q35)
    ("ai_vs_human_likert", {
        "title": "AI vs Human Comparison",
        "background": "comparison",
        "scale": "likert",
        "questions": [
            "For personal or emotional problems, I trust human advice more than AI-generated advice.",    # Reverse
            "Compared with humans, AI may provide more unbiased emotional support.",
            "If I had to choose one source of emotional support, I would usually choose a human over AI.",  # Reverse
        ],
    }),

    # AI vs Human Comparison — Hypothetical Scenarios (Q36–Q41)
    ("ai_vs_human_scenarios", {
        "title": "AI vs Human — Hypothetical Scenarios",
        "subtitle": (
            "For each situation below, indicate whom you would trust more for emotional support.\n"
            "1 = Trust Human Much More · 4 = Trust Both Equally · 7 = Trust AI Much More"
        ),
        "background": "comparison",
        "scale": "ai_vs_human",  # uses AI_VS_HUMAN_LABELS (7-point)
        "questions": [
            "When you feel emotionally low or lonely, whom would you trust more to talk to?\n(Human: emotional understanding · AI: available anytime)",
            "When you are stressed about studies, work, or your future, whom would you trust more for support?\n(Human: experience-based advice · AI: quick, structured guidance)",
            "When you are facing a family or relationship issue, whom would you trust more to discuss it with?\n(Human: understands personal context · AI: neutral, unbiased responses)",
            "When you need non-judgmental advice, whom would you trust more?\n(Human: empathetic listening · AI: non-judgmental interaction)",
            "When you want to share something deeply personal, whom would you trust more?\n(Human: emotional reassurance · AI: anonymous, private sharing)",
            "When you need ongoing emotional support over time, whom would you trust more?\n(Human: long-term connection · AI: consistent, always available)",
        ],
    }),

    # Future Use of AI for Emotional Support (Q42–Q44)
    ("future_use", {
        "title": "Future Use of AI for Emotional Support",
        "background": "future",
        "scale": "likert",
        "questions": [
            "Over the next 10 years, AI is likely to become a common and widely accepted source of emotional support.",
            "I am comfortable with my close ones relying on AI for emotional support.",
            "I think I will use AI for emotional support in the future.",
        ],
    }),
])


# ---------------------------------------------------------------------------
# Scale lookup helper — maps scale key to label dict
# ---------------------------------------------------------------------------
SCALE_LABELS = {
    "likert": LIKERT_LABELS,
    "ai_vs_human": AI_VS_HUMAN_LABELS,
}

def get_scale_for_section(section_data: dict) -> dict:
    """Return the appropriate label dict for a section's scale type."""
    scale_key = section_data.get("scale", "likert")
    return SCALE_LABELS.get(scale_key, LIKERT_LABELS)

def get_scale_size(section_data: dict) -> int:
    """Return the number of points for a section's scale (5 or 7)."""
    scale_key = section_data.get("scale", "likert")
    labels = SCALE_LABELS.get(scale_key, LIKERT_LABELS)
    return len(labels)


def _section_question_ids(sections):
    """Return ordered list of question IDs from an OrderedDict of sections."""
    ids = []
    for key, data in sections.items():
        for i in range(len(data["questions"])):
            ids.append(f"{key}_Q{i + 1}")
    return ids


def build_horizontal_columns():
    """
    Build the full ordered column list for horizontal (one-row-per-participant)
    spreadsheet format. Includes a superset of all possible question IDs so
    both User and Non-User rows fit the same header.

    Column order:
        metadata → demographics → personality → non-user-only → user-only → open-ended
    """
    meta = ["participant_id", "group", "started_at", "completed_at", "duration_seconds"]
    demo = [d["id"] for d in DEMOGRAPHICS]
    personality = _section_question_ids(PERSONALITY_SECTION)

    # Non-User only
    non_user_special = [NON_USE_REASONS["id"]]
    non_user_likert = _section_question_ids(NON_USER_SECTIONS)

    # User only
    user_special = [q["id"] for q in USER_USAGE_QUESTIONS]
    user_likert = _section_question_ids(USER_SECTIONS)

    # Open-ended (optional)
    open_ended = ["open_ended_Q1"]

    return (
        meta
        + demo
        + personality
        + non_user_special + non_user_likert
        + user_special + user_likert
        + open_ended
    )


# Pre-built column list for import convenience
HORIZONTAL_COLUMNS = build_horizontal_columns()
