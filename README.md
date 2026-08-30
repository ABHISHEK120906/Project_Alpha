# 🌟 FreelanceHub & Intelligence Platform (Project Alpha)

<div align="center">

![Platform Banner](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-6.0.7-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20DB-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Vercel](https://img.shields.io/badge/Deploy-Vercel%20Serverless-black?style=for-the-badge&logo=vercel&logoColor=white)

### **Manage. Connect. Analyze. Predict. Grow.**
**Full-Stack Marketplace • Freelancer Intelligence • Data Science • Business Intelligence**

</div>

---

## 📖 Executive Overview

**Project Alpha (FreelanceHub)** is an end-to-end, enterprise-grade ecosystem that bridges a **two-sided freelancing marketplace** (Clients & Freelancers) with an **advanced intelligence and predictive analytics suite**.

It unifies client relationship management (CRM), talent acquisition, KYC verification, project collaboration workspaces, statistical exploratory data analysis (EDA), time-series machine learning forecasting, and automated executive reporting into a unified, glassmorphic platform.

---

## 📐 Platform Architecture & Flow

```
                                  ┌──────────────────────────────────────────────────┐
                                  │           FREELANCEHUB ECOSYSTEM                 │
                                  │      Marketplace + Intelligence Platform         │
                                  └────────────────────────┬─────────────────────────┘
                                                           │
        ┌──────────────────────────────────────────────────┼──────────────────────────────────────────────────┐
        │                                                  │                                                  │
        ▼                                                  ▼                                                  ▼
┌───────────────────────────────┐          ┌───────────────────────────────┐          ┌───────────────────────────────┐
│        CLIENT PORTAL          │          │       FREELANCER PORTAL       │          │      ADMIN & DISPUTES         │
│   • Post & Manage Projects    │          │   • Discover & Filter Gigs    │          │   • Platform Governance       │
│   • Review Talent & Proposals │ ◄──────► │   • Submit Proposals          │ ◄──────► │   • User Account Auditing     │
│   • Milestone Progress Track  │          │   • Multi-Tier KYC Center     │          │   • Dispute Arbitration       │
│   • Escrow & Invoice Payments │          │   • Execution Workspaces      │          │   • Moderation & Export Hub   │
└───────────────┬───────────────┘          └───────────────┬───────────────┘          └───────────────┬───────────────┘
                │                                          │                                          │
                └──────────────────────────────────────────┼──────────────────────────────────────────┘
                                                           │
                                                           ▼
                                  ┌──────────────────────────────────────────────────┐
                                  │       INTELLIGENCE & ANALYTICS ENGINE            │
                                  │  • Statistical EDA (Descriptive, Quartiles, IQR) │
                                  │  • Outlier Detection (Tukey 1.5x, Z-Score > 2.2) │
                                  │  • Pearson Correlation Matrix (Heatmap)          │
                                  │  • Time-Series Forecasting (Holt-Winters + OLS)  │
                                  │  • Welch's Two-Sample t-Test Hypothesis Testing  │
                                  │  • Executive PDF (ReportLab) & Excel (openpyxl)  │
                                  └──────────────────────────────────────────────────┘
```

---

## 🚀 Core Pillars & Key Capabilities

### 1. 💼 Two-Sided Freelancing Marketplace

#### 🏢 Client Portal (`/client/`)
- **Job Creation & Publishing**: Post detailed project listings with budget ranges, milestones, deadlines, attachments, and required skills.
- **Proposal Review & Comparison**: Compare freelancer bids, delivery timelines, portfolios, and credibility badges.
- **Trust & Verification Badges**: View freelancer security levels (Email Verified, Phone Verified, Government ID, Tax PAN, Payment Verified).
- **Interactive Project Workspace**: Direct collaboration hub, milestone sign-offs, and project status transitions (*Open → In Progress → Completed*).
- **Ratings & Reviews**: Transparent rating system with feedback after project completion.

#### 👨‍💻 Freelancer Portal (`/freelancer/`)
- **Project Discovery & Search**: Filter projects by category, budget range, skill requirements, and project scope.
- **Proposal Management**: Submit customized proposals with pricing, estimated delivery, and milestone breakdowns.
- **Multi-Step KYC Verification Center**:
  - 📧 Email verification
  - 📱 Phone OTP verification
  - 🪪 Government ID verification
  - 📋 PAN / Tax card validation
  - 💳 Payment method verification
- **Active Workspace & Progress Tracking**: Real-time progress bar slider, deliverable notes, and direct client communications.
- **Financial Ledger & Invoices**: Track earnings, pending milestones, and completed disbursements.

#### 🛡️ Super Admin & Governance Portal (`/admin-dashboard/marketplace/`)
- **Platform Health KPI Dashboard**: Real-time metrics on registered users, active projects, escrow volumes, and dispute ratios.
- **User Moderation**: 1-click account suspension, reactivation, and verification auditing.
- **Dispute Resolution Center**: Structured dispute intake, evidence investigation, and arbitrator settlement tools.
- **Administrative Exports**: Multi-format data exports (CSV, Excel, PDF) across users, projects, and transactions.

---

### 2. 📊 Data Analytics & Exploratory Data Analysis (EDA)

- **Data Profiling Matrix**: Automated inspection of datasets (data types, non-null counts, null %, unique cardinality, min, max, mean, median, std dev).
- **Data Quality Scorecard**: Empirical health scoring ($0 - 100\%$) highlighting missing budgets, deadline discrepancies, and 1-click automated normalization.
- **Statistical Summaries**:
  - Sample Size ($N$), Mean, Median ($Q_2$), Mode, Range
  - Variance, Sample Standard Deviation ($s$), Interquartile Range ($IQR = Q_3 - Q_1$)
  - Percentile analysis ($P_{10}$, $P_{25}$, $P_{75}$, $P_{90}$) and Skewness classification.
- **Outlier Detection**: Tukey's IQR boxplot rule ($1.5 \times IQR$) paired with standard score ($|z| > 2.2$) outlier filters.
- **Correlation Matrix**: Multi-variable Pearson correlation coefficients with heatmap visualizations.
- **Granular Drill-Down Engine**: Interactive asynchronous drill-down modals powered by `/api/v1/analytics/drilldown/`.

---

### 3. 🧠 Data Science & Predictive Intelligence

- **Time-Series Revenue Forecasting**: 1–6 month future cash-flow projections using an ensemble of **Holt's Linear Exponential Smoothing** ($\alpha=0.35, \beta=0.15$) and **Ordinary Least Squares (OLS)** linear drift with 95% confidence intervals.
- **Hypothesis Testing (Welch's t-Test)**: Rigorous two-sample t-test comparing budgets of completed vs. in-progress contracts with t-stat, degrees of freedom, and p-value evaluation.
- **Predictive Risk & Delay Classifier**: Supervised logistic model estimating project delay probabilities based on scope, milestones, and budget.
- **Scenario Simulator**: Interactive sandbox to test "what-if" contract timelines, risk scoring, and delivery targets.
- **Small-Sample Guard**: Built-in safeguards requiring $N \ge 5$ observations to prevent misleading statistical claims.

---

### 4. 📑 Enterprise Reporting & Multi-Format Exports

- **Executive PDF Dossier (ReportLab)**: High-resolution, multi-page PDF documents containing executive KPIs, statistical charts, forecasting tables, and strategic recommendations.
- **Multi-Tab Excel Workbooks (openpyxl)**: Structured `.xlsx` spreadsheets with dedicated sheets for *Summary*, *Projects*, *Payments*, *Clients*, and *Forecasts* with custom cell formatting.
- **CSV Data Feeds**: Fast, streaming CSV exports for raw data pipelines.

---

## 🛠️ Technology Stack

| Domain | Technologies |
|---|---|
| **Backend** | Python 3.12, Django 6.0.7, Django REST Framework (DRF) |
| **Database** | PostgreSQL (Neon DB via `dj-database-url`), SQLite (Local dev) |
| **Data Analytics** | Python Standard Library (`math`, `statistics`, `collections`, `datetime`), Django ORM Aggregations |
| **Data Science** | Holt-Winters Smoothing, OLS Linear Regression, Welch's t-Test, Logistic Classifiers |
| **Reporting** | ReportLab (PDF), openpyxl (Excel), CSV engine |
| **Frontend** | Vanilla HTML5/CSS3 Design System, Glassmorphic UI Tokens, Chart.js 4.4.0, Lucide Icons |
| **Authentication** | Django Auth, OAuth 2.0 / Social Auth (Google, GitHub, LinkedIn), Role-Based Access Control (RBAC) |
| **Security & Ops** | WhiteNoise, CORS Headers, Custom Rate Limiting & Security Headers Middleware, Vercel Serverless |

---

## 📁 Repository Structure

```text
Project_Alpha/
├── core/                               # Core Intelligence & Freelancer Platform
│   ├── services/                       # Business Logic & Algorithms
│   │   ├── analytics_engine.py         # Profiling, EDA, Descriptive Stats, Outliers
│   │   ├── data_science_service.py     # Forecasting, ML Models, Hypothesis Testing
│   │   └── report_generator.py         # PDF (ReportLab) & Excel (openpyxl) Engine
│   ├── models.py                       # Core Relational Schemas (Projects, Payments, Clients)
│   ├── views.py                        # Analytics & Platform Views
│   ├── api_views.py                    # RESTful Endpoints (/api/v1/)
│   └── forms.py                        # Validation & Input Forms
├── marketplace/                        # Two-Sided Marketplace System
│   ├── models.py                       # Profiles, Marketplace Projects, KYC, Proposals, Disputes
│   ├── views.py                        # Client Portal Controllers
│   ├── views_freelancer.py             # Freelancer Portal & KYC Controllers
│   ├── views_admin.py                  # Admin Governance & Dispute Controllers
│   ├── urls.py                         # Client Portal Routes (/client/)
│   ├── urls_freelancer.py              # Freelancer Portal Routes (/freelancer/)
│   └── urls_admin.py                   # Admin Portal Routes (/admin-dashboard/marketplace/)
├── social_auth/                        # Social OAuth & Multi-Provider Auth Module
├── freelancer_tracker/                 # Django Root Settings, Middleware, WSGI
├── static/                             # Frontend Design System & Static Assets
│   ├── css/custom.css                  # Design Tokens, Glassmorphism & Themes
│   ├── js/analytics_workspace.js       # Chart.js Analytics Interactivity
│   └── js/data_science_workspace.js    # Forecasting Visualizers & Simulator
├── templates/                          # HTML5 UI Templates
│   ├── marketplace/                    # Client & Marketplace Views
│   ├── freelancer/                     # Freelancer Portal & KYC Templates
│   ├── admin_marketplace/              # Admin Moderation & Dispute Templates
│   ├── analytics/                      # Data Analytics Dashboards
│   └── data_science/                   # Predictive Modeling Dashboards
├── requirements.txt                    # Project Dependencies
└── vercel.json                         # Serverless Deployment Config
```

---

## 🚀 Getting Started Locally

### 1. Clone the Repository
```bash
git clone https://github.com/ABHISHEK120906/Project_Alpha.git
cd Project_Alpha
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secure-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### 5. Run Migrations & Launch Server
```bash
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Testing Suite

Execute the test suite to verify marketplace workflows, registration, and data services:
```bash
python manage.py test marketplace core
```

---

## 🔐 Security & Governance

- **Strict RBAC**: Complete isolation between Client, Freelancer, and Administrator permissions.
- **Secure Authentication**: Passwords hashed with PBKDF2 SHA-256; CSRF tokens enforced on all state modifications.
- **Middleware Protections**: Custom rate limiting, X-Frame-Options, Content Security Policies (CSP), and HSTS.
- **Safe Verification Flow**: Sensitive KYC documents are restricted to authorized administrators.

---

## 📄 License

This project is developed as part of **Project Alpha**. All rights reserved.
