# JUDAS — Adversarial Fraud Disruptor

> *Detect. Engage. Exhaust.*

JUDAS is an AI-powered tool that fights back against AI-assisted fraud by doing what a scammer least expects: wasting their time.

---

## The Problem

Scammers today use AI to generate personalised, high-volume fraud at scale — phishing messages, investment scams, impersonation attacks — targeting thousands of victims simultaneously at near-zero cost. The economics of mass fraud depend on fast, compliant targets. A cooperative victim takes seconds to exploit. The scammer moves on.

JUDAS flips that equation.

---

## What JUDAS Does

JUDAS acts as an adaptive AI respondent that intercepts scam messages and replies in a way that appears cooperative but deliberately wastes the scammer's time and processing effort. Instead of ignoring or blocking the scam, JUDAS engages — asking confused questions, introducing obstacles, requesting clarification, demanding written confirmation — keeping the scammer occupied while they get nothing in return.

The longer JUDAS holds a scammer's attention, the fewer real victims they can reach.

---

## How It Makes the World More Resilient

| Without JUDAS | With JUDAS |
|---|---|
| Scammer sends 1000 messages, gets 50 compliant replies in minutes | Scammer spends significant time per target with zero yield |
| AI-generated fraud is cheap and fast | Fraud becomes expensive in time and effort |
| Victims comply and lose money | JUDAS occupies the scammer's pipeline |

Every minute a scammer spends on JUDAS is a minute they are not spending on a real victim. At scale, this makes AI-powered fraud economically unviable.

---

## Architecture

JUDAS is built as a modular Python application with a Streamlit interface.

```
JUDAS/
├── main.py                  # Streamlit UI — orchestrates all modules
├── config.py                # Models, strategies, pricing constants
├── data/
│   └── scenarios.json       # Scam and normal scenario definitions
└── modules/
    ├── sentry.py            # Scam detection — scores and classifies input
    ├── brain.py             # LLM interface — JUDAS and Baseline responses
    ├── strategy_engine.py   # Rotating engagement strategies
    ├── taximeter.py         # Token and effort estimation
    ├── engagement_tracker.py# Turn tracking and session status
    └── session_manager.py   # Session lifecycle management
```

### Module Responsibilities

**Sentry** — Analyses incoming text using weighted keyword detection across phishing, crypto fraud, impersonation, and urgency signals. Returns a scam score (0–1) and scam type.

**Brain** — Calls the Groq LLM API. Supports two modes:
- `judas`: adaptive, evasive responses guided by the active strategy
- `baseline`: brief, cooperative responses simulating a trusting victim

**Strategy Engine** — Rotates through five engagement strategies as the conversation progresses:
1. **Naive Inquiry** — Plays confused, asks simple innocent questions
2. **Technical Expansion** — Requests reference numbers, callback numbers, supervisor names
3. **Constraint Injection** — Introduces personal obstacles to delay action
4. **Recursive Clarification** — Loops back and re-asks earlier questions
5. **Format Enforcement** — Demands written confirmation or email records

**Taximeter** — Estimates token usage per response and calculates an effort multiplier — how much harder JUDAS makes it for the scammer compared to a cooperative target.

**Engagement Tracker** — Monitors turn count, message count, and detects when a scammer disengages.

---

## Baseline vs JUDAS — The Comparison

A key feature of JUDAS is measurable proof of impact. Every JUDAS session is compared against a Baseline session run on the same scenario.

- **Baseline** simulates a trusting, cooperative respondent — brief replies, no resistance
- **JUDAS** uses rotating adaptive strategies to maximise scammer effort

The **Effort Multiplier** quantifies the difference:

```
Effort Multiplier = JUDAS total tokens ÷ (turns × baseline tokens per turn)
```

An effort score of 4x means the scammer had to process four times more content than they would have with a cooperative target — for zero result.

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/judas.git
cd judas

# Create and activate a virtual environment
python -m venv judas
# Windows
judas\Scripts\activate
# macOS / Linux
source judas/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_api_key_here
```

### Run

```bash
streamlit run main.py
```

Open your browser at `http://localhost:8501`.

---

## Usage

1. **Select Baseline mode** — choose a scam scenario from the dropdown
2. **Simulate a conversation** — click Simulate Reply to generate scammer messages, click Send to respond as a cooperative baseline victim
3. **Click Bye** to end the baseline session and note the token count
4. **Switch to JUDAS mode** — the same scenario is automatically loaded
5. **Run the same conversation** — JUDAS responds with adaptive strategies
6. **Click Bye** — the Session Analysis table compares JUDAS vs Baseline with the Effort Multiplier score

---

## Models Supported

| Model | Use |
|---|---|
| Llama 3.3 70B | Best quality (default) |
| Llama 3.1 8B | Fast fallback if rate limited |
| Llama 4 Scout 17B | Alternative |

Switch models from the sidebar without restarting.

---

## Stack

- **Python 3.10+**
- **Streamlit** — UI
- **Groq API** — LLM inference (Llama models)
- **python-dotenv** — environment config
- **pandas** — comparison table rendering

---

## Scenarios Included

| Scenario | Type |
|---|---|
| Fake Investment Offer | Scam |
| Account Verification Scam | Scam |
| IRS Impersonation | Scam |
| Tech Support Scam | Scam |
| Lottery Winning Scam | Scam |
| Friendly Check-in | Normal |
| Company Reaching Out to Customer | Normal |

Scam scenarios are AI-generated fresh each session — no hardcoded scripts.

---

## Limitations

- Effort Multiplier is token-based, not time-based — actual scammer time cost will vary
- Sentry detection is heuristic (keyword-based); it can miss novel scam patterns
- JUDAS is a research and demonstration tool — not a deployed real-time interception system

---

## License

MIT
