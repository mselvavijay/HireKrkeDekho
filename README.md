<div align="center">

  <img src="static/hirekrkedekho-logo.png" alt="HireKrkeDekho Logo" width="240" />

  <br>

  <h3>Architect Your Career Leap With AI — Calibrated to Your Exact Tech Stack</h3>

  [![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791.svg?logo=postgresql&logoColor=white)](https://supabase.com/)
  [![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black.svg?logo=vercel&logoColor=white)](https://hirekrkedekho.vercel.app)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

  <p align="center">
    <b>A high-performance, precision engineering career calibration platform.</b><br>
    Stop keyword guesswork. Get matched on degree, experience, and verified technical skills,<br>
    compete in daily 15-second timed engineering arena contests, and unlock customized 3-week transition roadmaps.
  </p>

  <p align="center">
    <a href="https://hirekrkedekho.vercel.app"><b>🌐 Live Platform</b></a> •
    <a href="#features"><b>✨ Features</b></a> •
    <a href="#tech-stack"><b>🛠 Tech Stack</b></a> •
    <a href="#architecture"><b>📐 Architecture</b></a> •
    <a href="#quickstart"><b>⚡ Quickstart</b></a> •
    <a href="#api-reference"><b>🔌 API Reference</b></a>
  </p>

  <br>

  <img src="static/hirekrkedekho-hero-3d-clean.png" alt="HireKrkeDekho Hero Showcase" width="92%" style="border-radius: 16px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);" />

</div>

---

<a id="why-hirekrkedekho"></a>
## 💡 Why HireKrkeDekho?

Traditional job portals drown candidates in keyword matching, unverified resumes, and ghost job listings. 

**HireKrkeDekho** replaces resume clutter with **tri-factor calibration** and **gamified engineering benchmarks**:
- **Tri-Factor Matching**: We calibrate your trajectory by cross-analyzing your degree, verified years of experience, and concrete skills rather than relying on arbitrary keywords.
- **Daily AI Arena (`/race/today`)**: Daily 15-question engineering challenges (15s per question) featuring real-time anti-cheat, speed scoring, live leaderboards, and candidate answer auditing.
- **3-Week Preparation Roadmaps**: Structured, milestone-driven roadmaps to fill technical gaps, build production-grade projects, and ace system design and live coding rounds.
- **Unslopped Pure-Web Performance**: 0% frontend framework overhead, pure vanilla ES6+ and modern CSS tokens, delivering sub-100ms interactive render speeds across both mobile and desktop browsers.

---

<a id="features"></a>
## ✨ Key Features

| Capability | Description |
| :--- | :--- |
| **🎯 Tri-Factor Precision Matching** | Simultaneously balances education level, seniority bracket, and specific tech stack components to recommend verified roles with real salary expectations. |
| **⚡ Daily Engineering Race** | 15 timed multiple-choice questions curated daily. Instant client-side validation, server-side tamper-resistant scoring, and automatic daily champion archival. |
| **📊 Admin Control Center (`/race/admin`)** | High-level analytics dashboard: track total attempts, live leaderboards, inspect candidate answer logs question-by-question, and export full reports to CSV. |
| **🤖 AI Career Advisory Workspace** | Context-aware consultation engine powered by high-throughput LLM backends (Groq) to answer architectural inquiries and recommend next career steps. |
| **🔐 Zero-Trust Auth Architecture** | Google Identity Services integration with server-issued HMAC-SHA256 authenticated cookies, stateless fallback tokens, and full account management. |
| **📱 Mobile-First Responsive Design** | Fluid layouts optimized across all viewport widths (320px to 1440px+), system dark-mode schemes, touch ergonomics, and safe-area insets. |

---

<a id="tech-stack"></a>
## 🛠 Tech Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Server:** [Uvicorn](https://www.uvicorn.org/) (ASGI)
- **Database & ORM:** [PostgreSQL](https://www.postgresql.org/) via [Supabase](https://supabase.com/) & [SQLAlchemy](https://www.sqlalchemy.org/)
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/latest/)
- **Auth & Crypto:** Google OAuth 2.0 Identity Services + HMAC-SHA256 session tokens

### AI & Integrations
- **AI Engine:** [Groq Cloud](https://groq.com/) for ultra-low latency structured career inference
- **Payments:** [Razorpay](https://razorpay.com/) integration for optional career advisory credits
- **Deployment:** [Vercel](https://vercel.com/) Serverless Python Runtime (`api/index.py`) + AWS ready

### Frontend
- **Markup & Layout:** Semantic HTML5 templates with [Jinja2](https://jinja.palletsprojects.com/)
- **Styling:** Vanilla CSS3 with custom design tokens (Electric Blue dark theme, zero CSS libraries)
- **Scripting:** Modular Vanilla JavaScript (ES6+), native Fetch API, dynamic smooth scroll handlers

---

<a id="architecture"></a>
## 📐 Architecture & System Flow

HireKrkeDekho operates on an asynchronous, decoupled architecture connecting candidate discovery, AI calibration, and real-time contest telemetry:

```mermaid
flowchart TD
    User([Candidate / Engineer]) -->|Tri-Factor Inputs: Degree, YOE, Skills| MatchEngine[Tri-Factor Match Engine]
    User -->|15s Daily Contest| RaceEngine[Daily Contest & Speed Tracker]
    User -->|Consultation Chat| Advisor[AI Career Advisor]

    subgraph CorePlatform [FastAPI Application Core]
        MatchEngine --> RoleMatch[Role & Seniority Calibration]
        RaceEngine --> AntiCheat[Anti-Cheat & Validation Engine]
        Advisor --> PromptGen[Prompt Generation & Roadmaps]
    end

    subgraph DataIntegrations [Data & External Services]
        RoleMatch --> Groq[Groq LLM Structured JSON]
        PromptGen --> Groq
        AntiCheat --> Postgres[(PostgreSQL / Supabase)]
        User -.->|OAuth 2.0| GoogleAuth[Google Identity Services]
        GoogleAuth --> SessionTokens[HMAC-SHA256 Auth Cookies]
    end

    subgraph TalentAnalytics [Talent & Contest Analytics]
        Postgres --> AdminRoom[Admin Control Room /race/admin]
        AdminRoom --> LeaderboardExport[Live Leaderboards & CSV Export]
    end
```

### 📁 Repository Structure

```text
HireKrkeDekho/
├── api/
│   └── index.py               # Vercel serverless entrypoint
├── routers/
│   ├── auth.py                # Google OAuth login, verification & session handling
│   ├── career.py              # LLM-powered consultation & structured recommendation engine
│   ├── chat.py                # Interactive consultation messaging endpoints
│   ├── health.py              # System healthchecks, DB ping & environment diagnostic
│   └── race.py                # Daily engineering contest, scoring engine & admin portal
├── static/
│   ├── app.css                # Unslopped, high-contrast dark theme stylesheet
│   ├── app.js                 # Frontend interactions, state sync & smooth scrolling
│   ├── hirekrkedekho-logo.png # Official brand logo
│   └── hirekrkedekho-hero-3d-clean.png # 3D Hero product showcase
├── templates/
│   ├── index.html             # Landing page, Tri-Factor explorer, Contest & About
│   ├── admin.html             # Daily contest analytics & candidate audit dashboard
│   ├── privacy.html           # Platform privacy policy
│   └── terms.html             # Terms of service
├── auth_token_service.py      # HMAC token generation, verification & cookie management
├── database.py                # SQLAlchemy DB engine, connection pooling & schema models
├── main.py                    # Root FastAPI application declaration & middleware
├── test_guardrails.py         # Automated regression & architecture test suite
└── requirements.txt           # Core Python dependencies
```

---

<a id="quickstart"></a>
## ⚡ Quickstart

### 1. Prerequisites
- **Python 3.11+** installed ([python.org](https://www.python.org/downloads/))
- **Git** installed ([git-scm.com](https://git-scm.com/))
- A free **Supabase** or PostgreSQL instance
- (Optional) Free API keys for **Groq** and **Google OAuth**

### 2. Clone the Repository
```bash
git clone https://github.com/mselvavijay/HireKrkeDekho.git
cd HireKrkeDekho
```

### 3. Create & Activate Virtual Environment
```bash
# macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# Windows:
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`):
```bash
cp .env.example .env
```

Configure the environment variables:
```env
# Database Connection (Supabase / Postgres)
DATABASE_URL=postgresql://postgres.user:password@aws-0-region.pooler.supabase.com:6543/postgres

# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com

# LLM Inference Key
GROQ_API_KEY=gsk_your_groq_api_key

# Daily Contest Settings
RACE_ENABLED=1
RACE_ADMIN_SECRET=your_secure_admin_secret_phrase
ADMIN_EMAILS=admin@yourdomain.com

# Payment Gateway (Optional)
RAZORPAY_KEY_ID=rzp_test_your_id
RAZORPAY_KEY_SECRET=your_secret_key
```

### 6. Run the Local Development Server
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000
```

---

<a id="tests"></a>
## 🧪 Running Automated Tests

HireKrkeDekho includes automated guardrail tests to guarantee endpoint stability, schema consistency, and security defaults.

Run all tests via pytest:
```bash
python -m pytest test_guardrails.py -v
```

---

<a id="api-reference"></a>
## 🔌 API Reference (Selected Endpoints)

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves main platform landing page & contest interface | Public |
| `GET` | `/health` | Application status, database readiness, and latency | Public |
| `POST` | `/auth/google` | Validates Google ID token & sets secure HMAC cookie | Public |
| `POST` | `/auth/signout` | Clears authenticated session cookies | Public |
| `GET` | `/race/today` | Fetches today's 15 timed challenge questions & status | Public / Candidate |
| `POST` | `/race/start` | Initiates timed contest session for the current candidate | Authenticated |
| `POST` | `/race/answer` | Validates and records question responses in real time | Authenticated |
| `GET` | `/race/admin` | Interactive admin KPI dashboard & candidate review | Admin Only |
| `GET` | `/race/admin/export` | Generates on-demand CSV of all contest participants | Admin Only |

---

<a id="contributing"></a>
## 🤝 Contributing

We welcome community contributions, bug reports, and feature suggestions!

1. **Fork** the repository on GitHub.
2. **Create a branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: Add question category filtering in race arena"
   ```
4. **Run the test suite** to ensure no regressions:
   ```bash
   python -m pytest test_guardrails.py
   ```
5. **Push** to your fork and submit a **Pull Request**.

---

<a id="license"></a>
## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">
  <sub>Crafted with passion for engineers, builders, and continuous learners.</sub><br>
  <sub><b>HireKrkeDekho</b> — Precision Career Acceleration.</sub>
</div>
