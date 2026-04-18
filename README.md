# JUDAS — Adversarial Fraud Disruptor

> *Making AI-powered fraud expensive, one wasted minute at a time.*
>
> Detect. Engage. Exhaust.

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
| Scammer sends 1,000 messages, gets 50 compliant replies in minutes | Scammer spends significant time per target with zero yield |
| AI-generated fraud is cheap and fast | Fraud becomes expensive in time and effort |
| Victims comply and lose money | JUDAS occupies the scammer's pipeline |

Every minute a scammer spends on JUDAS is a minute they are not spending on a real victim. At scale, this makes AI-powered fraud economically unviable.

---

## Architecture

JUDAS is built as a modular Python application with a Streamlit interface.

```
JUDAS/
├── main.py                   # Streamlit UI — orchestrates all modules
├── config.py                 # Models, strategies, pricing constants
├── data/
│   └── scenarios.json        # Scam and normal scenario definitions
└── modules/
    ├── sentry.py             # Scam detection — scores and classifies input
    ├── brain.py              # LLM interface — JUDAS and Baseline responses
    ├── strategy_engine.py    # Rotating engagement strategies
    ├── taximeter.py          # Token and effort estimation
    ├── engagement_tracker.py # Turn tracking and session status
    └── session_manager.py    # Session lifecycle management
```

### Module Responsibilities

**Sentry** — Analyses incoming text using weighted keyword detection across phishing, crypto fraud, impersonation, and urgency signals. Returns a scam score (0–1), scam type, and a colour-coded Detection Confidence level (High / Medium / Low).

**Brain** — Calls the Groq LLM API. Supports two modes:
- `judas`: adaptive, evasive responses guided by the active strategy
- `baseline`: brief, cooperative responses simulating a trusting victim

**Strategy Engine** — Rotates through five engagement strategies as the conversation progresses:

| # | Strategy | Turns | What it does |
|---|---|---|---|
| 1 | Naive Inquiry | 1 | Plays confused, asks simple innocent questions |
| 2 | Technical Expansion | 2–3 | Requests reference numbers, callback numbers, supervisor names |
| 3 | Constraint Injection | 4–5 | Introduces personal obstacles to delay action |
| 4 | Recursive Clarification | 6–7 | Loops back and re-asks earlier questions |
| 5 | Format Enforcement | 8+ | Demands written confirmation, email, or physical address |

**Taximeter** — Estimates token usage per response and calculates an Effort Multiplier — how much harder JUDAS makes it for the scammer compared to a cooperative target.

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

The **Scammer Time (est.)** row estimates actual time cost at ~90 seconds per turn. The **Scale Impact** panel shows how this compounds: at 1,000 intercepts per day, even a modest effort score wastes hundreds of scammer-hours daily.

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/KarthikSubramanian07/judas.git
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
2. **Simulate a conversation** — click **Simulate Reply** to generate a realistic scammer follow-up, click **Send** to respond as a cooperative baseline victim
3. **Click Bye** — a confirmation popup appears; note the token count in the Session Metrics box
4. **Switch to JUDAS mode** — the same scenario is automatically loaded and the dropdown is locked to ensure a fair comparison
5. **Run the same conversation** — JUDAS responds with adaptive rotating strategies; watch the Strategy card in the Session Metrics box change as turns progress
6. **Click Bye** — the Session Analysis table appears automatically, comparing JUDAS vs Baseline across turns, tokens, effort multiplier, estimated scammer time, and outcome
7. **Read the Scale Impact panel** — see how the effort score compounds at 100 and 1,000 daily intercepts

---

## Key UI Features

| Feature | Description |
|---|---|
| Detection Confidence badge | Colour-coded High / Medium / Low indicator on every scam message |
| Session Metrics box | Compact live cards for Turn, Messages, Status, Tokens, Strategy, and Effort — updates after every turn |
| Effort Multiplier (ⓘ) | Hover tooltip shows the full calculation with actual numbers |
| Strategy (ⓘ) | Hover tooltip describes all five strategies and their turn ranges |
| Scammer Time (est.) | Analysis table row estimating real-time cost at ~90s per turn |
| Scale Impact panel | Projects effort score to 100 and 1,000 daily intercepts |
| JUDAS is thinking… | Inline status message below metrics during response generation |
| Baseline complete popup | Green overlay after Baseline bye prompts user to switch to JUDAS mode |

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
| Friendly Check-in | Normal (JUDAS does not engage) |
| Company Reaching Out to Customer | Normal (JUDAS does not engage) |

Scam scenarios are AI-generated fresh each session — no hardcoded scripts. Normal scenarios are blocked in JUDAS mode as there is nothing adversarial to engage with.

---

## Limitations

- Effort Multiplier is token-based; the Scammer Time estimate assumes ~90 seconds per turn and will vary in practice
- Sentry detection is heuristic (keyword-based); novel scam patterns may score lower than expected
- JUDAS is a research and demonstration tool — not a deployed real-time interception system

---

## License

MIT
