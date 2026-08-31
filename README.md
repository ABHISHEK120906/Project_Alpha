# 🚀 Project Alpha (FreelanceHub)

A full-stack freelancing marketplace and smart business intelligence platform built with **Django** and **Python**.

FreelanceHub connects **Clients** who want to get work done with **Freelancers** looking for gigs, while providing smart analytics, project tracking, earnings forecasting, and professional PDF/Excel reporting.

---

## 🌟 Why FreelanceHub?

Unlike simple job boards, FreelanceHub gives you:
- **A Complete Marketplace**: Post jobs, apply for gigs, manage milestones, and track payments.
- **Trust & Verification**: Multi-step identity verification (KYC) for freelancers to prevent fraud.
- **Smart Data Analytics**: Real-time project charts, completion rates, and spending stats.
- **Future Forecasting**: AI/Data Science tools to predict project delivery risks and revenue trends.
- **One-Click Reports**: Export complete client & project dossiers directly to PDF or Excel.

---

## 🎯 Key Features

### 👤 1. Client Portal
- **Post Jobs Easily**: Create projects with custom budgets, required skills, and deadlines.
- **Review Proposals**: Compare freelancer bids, delivery times, and verification badges.
- **Track Progress**: Live workspace to monitor work status, milestone sign-offs, and ratings.
- **Hire & Manage**: Accept proposals and collaborate seamlessly in one dashboard.

### 💼 2. Freelancer Portal
- **Find Gigs**: Search and filter projects by category, budget, and skill requirements.
- **Send Proposals**: Submit custom pricing quotes and estimated delivery times.
- **KYC Verification**: Build trust by verifying Email, Phone OTP, Government ID, and Payment info.
- **Earnings & Workspaces**: Update project progress sliders and track completed payouts.

### 🛡️ 3. Admin & Governance Portal
- **Platform Overview**: Live stats on active users, open projects, and transactions.
- **User Moderation**: Verify freelancer documents, suspend or activate accounts.
- **Dispute Resolution**: Review and resolve client-freelancer disputes fairly.
- **Data Export**: Download platform data anytime in CSV, Excel, or PDF.

### 📊 4. Smart Analytics & Forecasting
- **Visual Dashboards**: Interactive charts powered by Chart.js showing budget distributions and project trends.
- **Income & Delivery Predictor**: Simple data models predicting future revenue and possible project delays.
- **Data Health Score**: Automatic check for missing deadlines or budget info.

### 📑 5. Instant Reports
- **Executive PDF Reports**: Clean, printable PDF summaries with charts and key metrics.
- **Excel (.xlsx) Spreadsheets**: Pre-formatted multi-tab workbooks (Projects, Payments, Clients).

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.12, Django 6.0 |
| **Frontend** | HTML5, CSS3 (Custom Responsive Design), JavaScript, Chart.js, Lucide Icons |
| **Database** | SQLite (Local Dev) / PostgreSQL (Neon DB for Cloud) |
| **Data & Reports** | ReportLab (PDF generator), openpyxl (Excel exports), Statistics & ML engine |
| **Authentication** | Django Auth, OAuth 2.0 (Google, GitHub, LinkedIn) |
| **Deployment** | Vercel Serverless Ready |

---

## 📁 Folder Structure

```text
Project_Alpha/
├── core/                   # Core business logic, analytics engine & report generators
│   ├── services/           # Analytics, ML forecasting, and PDF/Excel export tools
│   ├── models.py           # Database models for projects, payments, and clients
│   └── views.py            # Analytics dashboard views and API endpoints
├── marketplace/            # Marketplace apps (Clients, Freelancers, Admin)
│   ├── models.py           # Profiles, proposals, KYC verification, disputes
│   ├── views.py            # Client portal views
│   ├── views_freelancer.py # Freelancer portal & KYC views
│   └── views_admin.py      # Admin dashboard & dispute resolution
├── social_auth/            # Google & GitHub login integration
├── freelancer_tracker/     # Main Django settings, URLs, and middleware
├── static/                 # CSS styles, JS scripts, images, and charts
├── templates/              # HTML template pages (Marketplace, Dashboards, Auth)
├── requirements.txt        # List of Python dependencies
├── manage.py               # Django management script
└── vercel.json             # Vercel deployment configuration
```

---

## ⚡ Quick Start (Run Locally)

Follow these simple steps to run the project on your computer:

### Step 1: Clone the repository
```bash
git clone https://github.com/ABHISHEK120906/Project_Alpha.git
cd Project_Alpha
```

### Step 2: Create a virtual environment & activate it

- **On Windows (PowerShell / Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

- **On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install required packages
```bash
pip install -r requirements.txt
```

### Step 4: Create `.env` file
Create a `.env` file in the root folder with:
```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Step 5: Setup database & create superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Step 6: Start the development server
```bash
python manage.py runserver
```

Now open your browser and visit: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** 🎉

---

## 🧪 Running Tests

To verify that all marketplace features and services are working properly, run:
```bash
python manage.py test marketplace core
```

---

## 🔒 Security Highlights

- **Role-Based Access**: Clients, Freelancers, and Admins can only view and manage their own allowed areas.
- **Secure Password Storage**: Industry-standard hashing algorithms (PBKDF2 SHA-256).
- **Protected Verification Files**: Freelancer KYC identity documents are strictly protected and only accessible to verified administrators.

---

## 📄 License

This project is created under **Project Alpha**. Free to use and customize for development and learning purposes.
