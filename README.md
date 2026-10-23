# 🚀 Project Alpha — FreelanceHub & Business Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-API-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_DB-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![SQLite](https://img.shields.io/badge/SQLite-Local_Dev-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Chart.js](https://img.shields.io/badge/Data_Viz-Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![OpenAI](https://img.shields.io/badge/AI_Chatbot-TrackBot-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Deployment](https://img.shields.io/badge/Deployment-Vercel_Ready-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

> **A Next-Generation Freelancing Marketplace, Freelance Business CRM, and AI-Powered Predictive Analytics Intelligence Engine.**

---

## 📑 Table of Contents

- [📌 Project Overview](#-project-overview)
- [✨ Key Pillars & Capabilities](#-key-pillars--capabilities)
- [🏛️ System Architecture](#-system-architecture)
- [🎭 User Roles & Workflows](#-user-roles--workflows)
  - [1. 💼 Freelancer Portal & 5-Step KYC](#1--freelancer-portal--5-step-kyc)
  - [2. 🏢 Client Portal & Project Management](#2--client-portal--project-management)
  - [3. 🛡️ Super Admin & Governance Portal](#3--super-admin--governance-portal)
  - [4. 📊 Freelancer Business Intelligence CRM](#4--freelancer-business-intelligence-crm)
  - [5. 🔬 Data Science & Predictive Analytics Engine](#5--data-science--predictive-analytics-engine)
  - [6. 🤖 TrackBot AI Assistant](#6--trackbot-ai-assistant)
- [🛠️ Technology Stack](#-technology-stack)
- [📂 Project Directory Structure](#-project-directory-structure)
- [⚡ Quick Start & Local Setup](#-quick-start--local-setup)
- [⚙️ Environment Configuration (`.env`)](#-environment-configuration-env)
- [🔌 REST API v1 Specification](#-rest-api-v1-specification)
- [🧪 Running Test Suites](#-running-test-suites)
- [🎯 Live Demo & Presentation Walkthrough Guide](#-live-demo--presentation-walkthrough-guide)
- [🔐 Security & Compliance](#-security--compliance)
- [🚀 Production Deployment (Vercel + Neon DB)](#-production-deployment-vercel--neon-db)
- [👥 Contributors & License](#-contributors--license)

---

## 📌 Project Overview

**Project Alpha (FreelanceHub)** is an end-to-end web platform designed to solve the two biggest challenges in the modern freelance economy:
1. **The Trust Deficit in Freelancing Marketplaces:** Clients fear fraudulent profiles and missed deadlines; freelancers struggle with delayed payments and unfair disputes.
2. **The Lack of Business Intelligence for Freelancers:** Freelancers often operate blind without knowing their delivery risks, revenue predictability, profit margins, or client retention stats.

FreelanceHub bridges this gap by unifying a **two-sided trust-first freelancing marketplace** (with automated 5-step KYC verification, milestone workspaces, and escrow-style payment logging) alongside an **enterprise-grade Data Science & Analytics CRM** that forecasts earnings, predicts project delays, produces executive PDF invoices, and integrates a 24/7 AI business assistant (**TrackBot**).

---

## ✨ Key Pillars & Capabilities

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             PROJECT ALPHA ECOSYSTEM                              │
├───────────────────────┬────────────────────────────┬─────────────────────────────┤
│   🤝 MARKETPLACE      │   📈 INTELLIGENCE & ML     │   🛡️ GOVERNANCE & AI        │
│ • Client Postings     │ • Holt-Winters Forecasting │ • 5-Step KYC Verification   │
│ • Freelancer Proposals│ • Project Risk Classifier  │ • Admin Dispute Arbitration │
│ • Milestone Workspace │ • Revenue Predictor        │ • TrackBot AI Chatbot       │
│ • Progress Sliders    │ • One-Click PDF/Excel Docs │ • OAuth 2.0 (Google/GitHub) │
│ • Review & Rating     │ • Data Health Auto-Cleaner │ • Audit Trail & Logs        │
└───────────────────────┴────────────────────────────┴─────────────────────────────┘
```

- **5-Stage Identity Verification (KYC):** Government ID upload, PAN card validation, Phone OTP simulation, Email check, and Bank/UPI verification.
- **Predictive Time-Series & Delay Models:** Statistical trend analysis, Holt-Winters exponential smoothing, and regression algorithms predicting project delivery risks and revenue runways.
- **Interactive Data Visualizations:** Real-time Chart.js interactive graphs for revenue streams, client distributions, and project statuses.
- **Automated Reporting Pipeline:** High-fidelity, multi-tab Excel (`.xlsx`) workbooks and branded executive PDF summaries using `ReportLab` and `openpyxl`.
- **Intelligent Assistant (TrackBot):** Conversational AI equipped to answer business inquiries, generate project summaries, and analyze portfolio performance.
- **Production & Serverless Ready:** Pre-configured for seamless deployment to Vercel with PostgreSQL (Neon DB) and local zero-config SQLite fallback.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User["🌐 End Users (Clients / Freelancers / Admins)"] --> UI["🖥️ Responsive Frontend (HTML5, Vanilla CSS, JS, Chart.js, Lucide)"]
    
    UI --> Routing["⚙️ Django 5.x URL Routing & Middleware"]
    
    subgraph Security Layer
        Routing --> Auth["🔐 Auth & Security (RBAC, Session Auth, OAuth 2.0 Google/GitHub)"]
        Auth --> KYC["🛡️ KYC & File Protection Service"]
    end
    
    subgraph Application Modules
        Routing --> CoreApp["📦 Core CRM & Analytics (Projects, Finances, Invoices, Notes)"]
        Routing --> MarketApp["🤝 Marketplace (Jobs, Proposals, Workspaces, Disputes)"]
        Routing --> API["⚡ REST API v1 (Django REST Framework)"]
        Routing --> AIChat["🤖 TrackBot AI (OpenAI API / LLM Engine)"]
    end
    
    subgraph Data & Computation Engine
        CoreApp --> DSEngine["🔬 Data Science Service (Forecasting, Risk Models, Metrics)"]
        CoreApp --> ReportEngine["📑 Report Engine (ReportLab PDF & openpyxl Excel)"]
    end
    
    subgraph Persistence Layer
        CoreApp --> DB[("🗄️ Database (Neon PostgreSQL / SQLite3)")]
        MarketApp --> DB
        API --> DB
        AIChat --> DB
    end
```

---

## 🎭 User Roles & Workflows

### 1. 💼 Freelancer Portal & 5-Step KYC
- **Gig Discovery & Search:** Real-time search and multi-facet filtering by category, budget tier, and required technical skills.
- **Proposal Submission:** Direct bid proposals with custom pricing quotes, milestone timelines, and portfolio references.
- **5-Step Security Verification Center (KYC):**
  1. *Email Verification*: Identity confirmation link / OTP.
  2. *Phone Verification*: SMS OTP simulation.
  3. *Government ID Upload*: Aadhaar / Passport / Driver's License file submission.
  4. *PAN Card Validation*: Format verification and tax compliance.
  5. *Payment Verification*: Bank details / UPI ID check for payout disbursement.
- **Active Workspace & Progress Slider:** Drag-and-drop status slider (0% to 100%) to communicate real-time progress to clients.
- **Financial Ledger:** Track pending earnings, released payments, and platform ratings.

### 2. 🏢 Client Portal & Project Management
- **One-Click Job Posting:** Specify technical requirements, milestone deliverables, project duration, and flexible budget ranges.
- **Applicant Review Board:** Evaluate freelancer profiles, view verified badge statuses, examine proposed delivery timelines, and compare bid amounts.
- **Hiring & Engagement:** Hire candidates with single-click acceptance; automatically initializes an isolated project workspace.
- **Milestone Oversight:** Approve project phases, sign off on deliverables, leave star reviews, and request revisions.
- **Financial Accounting:** Overview of all spending, invoices, and dispute filing support.

### 3. 🛡️ Super Admin & Governance Portal
- **Executive KPI Dashboard:** Real-time counters for platform revenue, user registrations, open projects, and active disputes.
- **User Moderation:** Full control to audit profiles, inspect uploaded KYC identification documents, approve verification badges, or suspend accounts violating terms.
- **Dispute Resolution Desk:** Objective arbitration for milestone disputes between clients and freelancers.
- **Multi-Format Export Hub:** Instant backup and export of entire platform logs in CSV, Excel, or PDF.

### 4. 📊 Freelancer Business Intelligence CRM
- **Task Management (Kanban & List):** Track tasks with priority flags, deadlines, and completion statuses.
- **Income & Expense Bookkeeping:** Categorized accounting for subscriptions, software tools, equipment, and client income.
- **Professional Invoicing Engine:** Generate branded, downloadable PDF invoices with taxes, payment receipts, and QR code/bank information.
- **Calendar & Event Scheduling:** Synchronized view of all approaching project deadlines and payment milestones.
- **Audit Activity Log:** Complete event timeline of every action taken in the workspace.

### 5. 🔬 Data Science & Predictive Analytics Engine
- **Time-Series Forecasting:** Uses Holt-Winters Exponential Smoothing, Linear Trend Projection, and Moving Averages to predict income 3 to 6 months out.
- **Project Delivery Risk Classifier:** Predicts whether a project is at risk of being delayed based on task velocity and historical client turnaround times.
- **Model Evaluation Metrics:** Displays true data science evaluation statistics:
  - Mean Absolute Error (**MAE**)
  - Root Mean Squared Error (**RMSE**)
  - Coefficient of Determination (**R²**)
  - Confusion Matrix, Accuracy, Precision, Recall, and F1-Score
- **Data Health Score & Auto-Cleaning:** Automated diagnostics to identify incomplete records, missing budgets, or orphaned milestones with one-click cleanup actions.

### 6. 🤖 TrackBot AI Assistant
- Integrated OpenAI-compatible chatbot assistant.
- Retains context across multi-turn conversations.
- Can draft client project proposals, summarize project statuses, compute profitability estimates, and offer business optimization tips.

---

## 🛠️ Technology Stack

| Layer | Technologies Used | Description / Purpose |
|---|---|---|
| **Backend Framework** | **Python 3.12**, **Django 5.0+** | Robust, scalable MVT backend architecture |
| **API Architecture** | **Django REST Framework (DRF)** | Standardized RESTful JSON endpoints |
| **Frontend** | **HTML5, CSS3, JavaScript (Vanilla ES6)** | Responsive, lightweight, modern UI without framework bloat |
| **Icons & Visuals** | **Lucide Icons**, **Chart.js** | Crisp iconography and interactive dynamic charts |
| **Relational Database** | **PostgreSQL (Neon DB)** / **SQLite3** | Production serverless SQL & zero-config local development |
| **Document Generation** | **ReportLab 4.x**, **openpyxl 3.x** | Custom PDF invoices and multi-tab Excel reports |
| **AI / Large Language Model** | **OpenAI API Client (`openai>=1.30.0`)** | Powers the intelligent TrackBot copilot |
| **Authentication** | **Django Auth**, **OAuth 2.0** | Secure sessions, PBKDF2 hashing, Google & GitHub login |
| **Static Assets** | **WhiteNoise 6.5+** | Efficient, edge-cached static file serving |
| **Deployment Target** | **Vercel Serverless Functions** | Instant cloud deployment with `vercel.json` |

---

## 📂 Project Directory Structure

```text
Project_Alpha/
├── core/                         # Core Business Logic, CRM & Analytics Engine
│   ├── admin_urls.py             # Super Admin dashboard URL mappings
│   ├── api_views.py              # REST API v1 endpoints for core platform
│   ├── models.py                 # Client, Project, Payment, Task, Invoice, Expense models
│   ├── services/                 # Algorithmic & Service Layers
│   │   ├── analytics_engine.py   # Aggregation & statistical analysis service
│   │   ├── data_science_service.py # Predictive models, Holt-Winters, ML evaluation
│   │   └── report_generator.py   # ReportLab PDF & openpyxl Excel generators
│   ├── views.py                  # Core CRM views & controllers
│   └── urls.py                   # Core routing rules
│
├── marketplace/                  # Marketplace & Two-Sided Platform
│   ├── models.py                 # FreelancerProfile, Proposal, KYCVerification, Disputes
│   ├── views.py                  # Client-facing portal views
│   ├── views_freelancer.py       # Freelancer portal views & KYC flow
│   ├── views_admin.py            # Marketplace governance & dispute management
│   ├── api_views.py              # Client REST APIs
│   ├── api_views_freelancer.py   # Freelancer REST APIs
│   ├── api_views_admin.py        # Super Admin REST APIs
│   ├── urls.py                   # /client/ URLs
│   ├── urls_freelancer.py        # /freelancer/ URLs
│   └── urls_admin.py             # /admin-dashboard/marketplace/ URLs
│
├── social_auth/                  # OAuth 2.0 Social Login (Google & GitHub)
├── freelancer_tracker/           # Django Application Settings & Core Routing
│   ├── settings.py               # Database, security, and app configurations
│   ├── urls.py                   # Master root URL dispatch table
│   └── wsgi.py                   # WSGI server gateway
│
├── static/                       # Static assets (Custom CSS stylesheets, JS scripts, icons)
├── templates/                    # Modular Django HTML Templates
│   ├── admin_dashboard/          # Super Admin moderation & statistics screens
│   ├── analytics/                # Business analytics & interactive dashboards
│   ├── chat/                     # TrackBot AI Chatbot interface
│   ├── clients/                  # Client CRM interfaces
│   ├── data_science/             # Predictive ML & statistical forecasting pages
│   ├── invoices/                 # Invoicing & PDF receipt views
│   ├── marketplace/              # Marketplace, KYC, and workspace screens
│   ├── projects/                 # Project Kanban & detail views
│   └── home.html                 # Hero landing page
│
├── requirements.txt              # Production Python package dependencies
├── manage.py                     # Django CLI management entrypoint
├── vercel.json                   # Vercel serverless deployment specifications
├── build_files.sh                # Vercel automated build script
└── README.md                     # Comprehensive project documentation
```

---

## ⚡ Quick Start & Local Setup

Get Project Alpha running on your local machine in under 5 minutes:

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **Git** installed on your system

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/ABHISHEK120906/Project_Alpha.git
cd Project_Alpha
```

---

### Step 2: Set Up Virtual Environment

- **On Windows (PowerShell / Command Prompt):**
```powershell
python -m venv venv
venv\Scripts\activate
```

- **On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables
Create a `.env` file in the root project folder:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env   # Or create a new .env file

# macOS / Linux
cp .env.example .env
```

If you don't have a `.env.example`, simply paste the following into a new `.env` file:
```env
SECRET_KEY=django-insecure-alpha-dev-key-change-in-production-123456
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Leave DATABASE_URL empty or commented out to automatically use local SQLite:
# DATABASE_URL=sqlite:///db.sqlite3

# Optional: TrackBot AI Chatbot (OpenAI key)
AI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4o-mini
```

---

### Step 5: Run Database Migrations
```bash
python manage.py migrate
```

---

### Step 6: Create an Administrator Account
```bash
python manage.py createsuperuser
```
*(Enter your desired username, email, and password when prompted).*

---

### Step 7: Launch the Development Server
```bash
python manage.py runserver
```

🎉 Open your browser and navigate to: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

> **💡 Pro Tip (Seed Sample Data):**  
> Once logged in, visit **[http://127.0.0.1:8000/seed-sample-data/](http://127.0.0.1:8000/seed-sample-data/)** to instantly populate realistic projects, payments, tasks, and analytics for live demonstration!

---

## ⚙️ Environment Configuration (`.env`)

| Variable | Required? | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | Built-in fallback | Django cryptographic signing key |
| `DEBUG` | **Yes** | `True` | Debug mode (`True` for local, `False` for production) |
| `ALLOWED_HOSTS` | **Yes** | `localhost,127.0.0.1` | Host/domain names that this Django site can serve |
| `DATABASE_URL` | Optional | SQLite fallback | PostgreSQL / Neon connection string (e.g. `postgresql://user:pass@host/db`) |
| `CSRF_TRUSTED_ORIGINS`| Optional | `http://localhost:8000` | Origins allowed to perform safe POST requests |
| `AI_API_KEY` | Optional | `""` | OpenAI API key for TrackBot chatbot |
| `AI_MODEL` | Optional | `gpt-4o-mini` | AI Model name (e.g. `gpt-4o-mini`, `gpt-4o`) |
| `CHAT_RATE_LIMIT_PER_HOUR` | Optional | `50` | Maximum chatbot messages per user per hour |

---

## 🔌 REST API v1 Specification

Project Alpha includes a robust suite of REST API endpoints built with Django REST Framework (DRF):

### 🏢 Client Endpoints (`/client/api/v1/`)
- `GET /client/api/v1/client/dashboard/stats/` — Real-time spending & project KPI statistics
- `GET /client/api/v1/client/projects/` — List all client projects
- `GET /client/api/v1/client/projects/<uuid>/applications/` — View applicants for a project
- `POST /client/api/v1/client/applications/<uuid>/accept/` — Hire freelancer / accept application
- `POST /client/api/v1/client/applications/<uuid>/reject/` — Reject candidate application
- `GET /client/api/v1/client/payments/` — Fetch client transaction history

### 💼 Freelancer Endpoints (`/freelancer/api/v1/`)
- `GET /freelancer/api/v1/dashboard/stats/` — Active bids, ongoing projects & earnings summary
- `GET /freelancer/api/v1/verification/status/` — Current 5-step KYC verification progress
- `POST /freelancer/api/v1/verification/verify-step/` — Submit step verification payload
- `GET /freelancer/api/v1/projects/` — Search and filter available marketplace gigs
- `POST /freelancer/api/v1/projects/<uuid>/apply/` — Submit bid proposal to client project
- `POST /freelancer/api/v1/my-projects/<uuid>/progress/` — Update project completion slider percentage

### 🛡️ Admin Endpoints (`/admin-dashboard/marketplace/api/v1/`)
- `GET /admin-dashboard/marketplace/api/v1/dashboard/stats/` — Global platform activity telemetry
- `POST /admin-dashboard/marketplace/api/v1/users/<id>/suspend/` — Ban or unsuspend user account
- `POST /admin-dashboard/marketplace/api/v1/projects/<uuid>/moderate/` — Approve / take down project posting
- `POST /admin-dashboard/marketplace/api/v1/disputes/<uuid>/resolve/` — Arbitrate dispute & allocate funds

### 🤖 TrackBot AI & Core Endpoints (`/api/v1/`)
- `GET /api/v1/dashboard/stats/` — Core CRM financial & task metrics
- `GET /api/v1/dashboard/analytics/` — Dynamic Chart.js dataset feeds
- `GET /api/v1/chat/conversations/` — Retrieve past AI conversation sessions
- `POST /api/v1/chat/send/` — Send prompt to TrackBot and receive AI response

---

## 🧪 Running Test Suites

Project Alpha comes with automated tests covering marketplace workflows, verification rules, and calculation engines:

```bash
# Run tests across core and marketplace modules
python manage.py test marketplace core

# Run tests with verbose output
python manage.py test -v 2
```

---

## 🎯 Live Demo & Presentation Walkthrough Guide

Use this recommended sequence when showcasing Project Alpha in an interview, college project viva, or investor pitch:

```
[1. Hero Landing Page] ──► [2. One-Click Sample Data] ──► [3. 5-Step KYC Verification]
          │                                                               │
          ▼                                                               ▼
[6. Executive PDF/Excel] ◄── [5. Data Science & ML Engine] ◄── [4. Active Workspace & Slider]
```

1. **The Landing Page (`/`):**
   - Showcase the modern dark-mode aesthetic, value proposition, and clean responsive layout.
2. **Instant Demo Setup (`/seed-sample-data/`):**
   - Click this link to automatically generate comprehensive demo data (clients, payments, tasks, and historical revenue).
3. **The Freelancer KYC Journey (`/freelancer/verification/`):**
   - Walk through the 5-step verification process. Highlight the Aadhaar/Government ID upload and PAN verification badges that build marketplace trust.
4. **Marketplace Discovery & Workspace (`/freelancer/find-projects/` & `/freelancer/my-projects/`):**
   - Show how a freelancer filters jobs and submits a proposal.
   - Switch to the client view to accept the proposal.
   - Demonstrate the **Live Progress Slider** where freelancers adjust completion percentage (e.g., 25% → 75%) and clients see it update instantly.
5. **Data Science & Predictive Intelligence (`/data-science/` & `/analytics/`):**
   - Present the **Holt-Winters Income Forecast** showing next quarter revenue projections.
   - Point out the **Project Delay Classifier** flagging at-risk milestones.
   - Explain the true data science metrics: **MAE, RMSE, R², Accuracy, and Confusion Matrix**.
   - Show the **Data Health Score** and demonstrate the auto-clean mechanism.
6. **Executive Reporting & Export (`/reports/`):**
   - Generate a one-click **Executive PDF Report** (using ReportLab) and open a multi-tab **Excel Workbook** (using openpyxl).
7. **TrackBot AI Assistant (`/chat/`):**
   - Ask TrackBot to summarize active project milestones or advise on pricing a freelance web development project.

---

## 🔐 Security & Compliance

- **Role-Based Access Control (RBAC):** Strict view-level decorators and queryset isolation ensuring users cannot access or alter other users' private data.
- **Protected KYC Storage:** Identity verification documents (passports, national IDs, PAN cards) are isolated and restricted exclusively to verified Super Admins.
- **Cryptographic Password Security:** Salted PBKDF2 with SHA-256 password hashing.
- **CSRF & Injection Defenses:** Universal CSRF tokens on all state-altering forms; Django ORM parameterized queries protecting against SQL injection.
- **Rate-Limiting on AI Endpoints:** Built-in hourly quotas (`CHAT_RATE_LIMIT_PER_HOUR`) to protect against API abuse and runaway costs.

---

## 🚀 Production Deployment (Vercel + Neon DB)

Project Alpha is configured for 100% serverless hosting on **Vercel** backed by **Neon PostgreSQL**:

1. **Push your code to GitHub.**
2. **Import the repository into Vercel.**
3. **Add Environment Variables in Vercel Project Settings:**
   - `SECRET_KEY` = *[Your production secret]*
   - `DEBUG` = `False`
   - `DATABASE_URL` = *[Your Neon PostgreSQL connection string]*
   - `ALLOWED_HOSTS` = `.vercel.app`
   - `CSRF_TRUSTED_ORIGINS` = `https://your-app-name.vercel.app`
4. **Deploy!** Vercel will automatically execute `build_files.sh`, gather static assets via WhiteNoise, and serve serverless function routes specified in `vercel.json`.

---

## 👥 Contributors & License

- **Lead Developer & Architect:** [Abhishek](https://github.com/ABHISHEK120906)
- **Repository:** [Project_Alpha on GitHub](https://github.com/ABHISHEK120906/Project_Alpha)
- **License:** Open Source under the MIT License — free for learning, development, and commercial enhancement.

---

<p align="center">
  <b>⭐ If you find this project impressive or helpful, please consider starring the repository! ⭐</b>
</p>
