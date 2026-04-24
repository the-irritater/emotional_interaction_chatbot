# Emotional Interaction with AI — Chatbot-Based Questionnaire System

A production-ready **Streamlit** web application for collecting structured research questionnaire responses through an interactive chatbot-style interface. Designed for academic research on emotional interaction with artificial intelligence.

---

## Features

- **Conversational Chatbot UI** — One question at a time with realistic typing animations and chat bubbles
- **Dark Navy & Purple Theme** — Premium glassmorphism design with ambient particle effects
- **Smart Flow** — Screening-first branching routes participants to the correct questionnaire path (User / Non-User)
- **7-Point Likert Scale** — Mobile-friendly scale with visible anchor labels on all screen sizes
- **Back Button** — One-step undo to correct accidental taps
- **Progress Tracking** — Real-time progress bar, percentage counter, and section-transition interstitials with progress ring
- **Dual Data Persistence** — Responses saved to Google Sheets (primary) + local CSV (backup) with per-response autosave
- **Conditional Completion** — Status-aware completion screen (green for cloud save, amber for local-only)
- **Optional Open-Ended Question** — Qualitative item at the end for richer research data
- **Participant Summary** — Separate worksheet tracking participant metadata, duration, and submission status
- **Privacy-First Design** — Anonymous participation with auto-generated participant IDs
- **Mobile Responsive** — Optimised for both desktop and mobile viewports with touch-friendly interactions
- **Download Option** — Participants can download their own responses after completion

---

## Flow

```
Welcome → Screening → Demographics → Questionnaire → Open-Ended (optional) → Completion
```

---

## Questionnaire Structure

### Non-User Path (20 questions · ~4–6 minutes)
| Section | Items |
|---|---|
| Perceived Capability of AI | 4 |
| Perceived Authenticity of AI | 4 |
| Openness Toward AI Interaction | 4 |
| Concerns and Skepticism | 4 |
| Human-to-Human Trust | 4 |

### User Path (49 questions · ~8–12 minutes)
| Section | Items |
|---|---|
| Motivation to Use AI | 14 |
| Perceived Empathy of AI | 7 |
| Perceived Authenticity in AI Interaction | 12 |
| Trust in AI | 12 |
| Human-to-Human Trust | 4 |

---

## Project Structure

```
emotional-ai-questionnaire/
├── .streamlit/
│   ├── config.toml          # Streamlit theme configuration
│   └── secrets.toml         # Google Sheets credentials (not committed)
├── assets/                   # Background images
│   ├── bg_capability.png
│   ├── bg_authenticity.png
│   ├── bg_openness.png
│   ├── bg_concerns.png
│   └── bg_trust.png
├── data/                     # CSV response storage (auto-created)
│   └── responses.csv
├── app.py                    # Main Streamlit application
├── questions.py              # Questionnaire data (ordered dictionaries)
├── utils.py                  # Helper functions, CSS system, data persistence
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## How to Run

### Prerequisites
- Python 3.9 or higher
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/the-irritater/emotional-ai-questionnaire.git
   cd emotional-ai-questionnaire
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   # venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. Open **http://localhost:8501** in your browser.

---

## Data Output

### Response Data (`responses.csv` / Google Sheets — Sheet1)

| Column | Description |
|---|---|
| `participant_id` | Unique anonymous ID (e.g., `P-3A7F2C01`) |
| `group` | `User` or `Non-User` |
| `section` | Questionnaire section name |
| `question_id` | Unique question identifier |
| `question_text` | Full question text |
| `response` | Numeric response (1–7) or text |
| `response_label` | Text label (e.g., "Strongly Agree") |
| `timestamp` | ISO 8601 timestamp |
| `started_at` | When the participant started |
| `completed_at` | When the participant finished |
| `duration_seconds` | Total time spent |

### Participant Summary (Google Sheets — "Participants" worksheet)

| Column | Description |
|---|---|
| `participant_id` | Unique anonymous ID |
| `group` | `User` or `Non-User` |
| `started_at` / `completed_at` | Session timestamps |
| `duration_seconds` | Total survey duration |
| `total_questions` / `total_answered` | Question counts |
| `submission_status` | `cloud_saved` or `local_only` |

---

## Deployment

### Streamlit Community Cloud

1. Push to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and deploy
4. Add secrets in the Streamlit Cloud dashboard (Settings → Secrets)

### Docker (optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

---

## Research Ethics

- All responses are anonymous — no PII is collected
- Question wording is preserved verbatim from the validated research instrument
- UI is designed to be neutral and non-biasing
- Informed consent notice is displayed before participation

---

## License

This project is developed for academic research purposes. Please cite appropriately if used in publications.

---

## Acknowledgements

Questionnaire items adapted from established scales in human–AI interaction research. See `questions.py` for full source citations.
