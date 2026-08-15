# FreelanceTrack — Freelancer Project Management System

A production-ready, feature-rich project management and productivity platform built specifically for freelancers and independent contractors. Track clients, projects, payments, tasks, financial flows, invoices, deadlines, and get AI-assisted insights with TrackBot — all in one unified workspace.

## 🚀 Tech Stack

- **Backend**: Django 6.0.7 + Django REST Framework (DRF)
- **Database**: PostgreSQL (Neon) via `dj-database-url` (SQLite for local fallback)
- **Authentication**: Custom Role-Based Authentication with Audit Logging & IP Security Controls
- **Static Files**: WhiteNoise with compression and caching
- **Deployment**: Vercel (Serverless Python) & WSGI Support
- **Reports & Invoicing**: ReportLab (PDF generation) + openpyxl (Excel exports)
- **Frontend**: Vanilla CSS + Glassmorphism UI + Chart.js Data Visualizations + Dark/Light Theme

---

## 🌟 Key Features

### 1. 🔐 Authentication & Security
- Secure registration and login workflows with data isolation per user.
- Super Admin Dashboard with login audit history, blocked IP management, and system metrics.
- User profile customization, avatar management, and password management.

### 2. 👥 Client & Project Management
- Full CRUD for clients with contact details, company tracking, and status filtering.
- Comprehensive project tracking (status, priority, progress bar, budget, deadlines).
- Project attachments, file manager, and discussion comment threads.
- Archive, restore, and 1-click duplicate project functionality.

### 3. 💳 Financials & Invoices
- Income and Expense tracking with categorized financial summaries and balance calculations.
- Professional Invoice generator with itemized line items, tax calculations, and status tracking.
- Instant PDF Invoice exports and email dispatch capabilities.
- Payment recording with receipt generation.

### 4. ✅ Tasks, Calendar & Time Tracking
- Task management with status toggles, priority flags, and deadlines.
- Integrated interactive Calendar for deadlines, milestones, and scheduled events.
- Project notes and quick memo scratchpad.

### 5. 🤖 TrackBot AI Assistant
- Interactive AI chat assistant for freelance productivity, project recommendations, and quick assistance.
- Multi-conversation history with persistent threads and conversation management.

### 6. 📊 Analytics & Reporting
- Dynamic dashboard with real-time Chart.js revenue, project status, and task progress charts.
- Exportable PDF and Excel reports for projects, earnings, and client activity.
- Complete activity audit log.

---

## 📁 Project Structure

```text
Project_Alpha/
├── core/                   # Main Django app (Models, Views, Forms, APIs, Tests)
│   ├── management/         # Custom management commands (seed data, admin setup)
│   ├── migrations/         # Database migrations
│   ├── admin_views.py      # Super Admin dashboard views
│   ├── api_views.py        # RESTful API endpoints
│   ├── models.py           # Database schema & entities
│   ├── forms.py            # Form validation & widgets
│   ├── views.py            # Core business logic & request handlers
│   └── urls.py             # App routing
├── freelancer_tracker/     # Project configuration & settings
│   ├── settings.py         # Django settings (Decouple & WhiteNoise)
│   ├── urls.py             # Root URL routing
│   └── wsgi.py             # WSGI entry point
├── social_auth/            # Social authentication handlers
├── static/                 # CSS, JavaScript & theme assets
├── templates/              # Jinja2 / Django HTML templates
├── manage.py               # Django CLI management script
├── requirements.txt        # Python package dependencies
└── vercel.json             # Vercel serverless deployment config
```

---

## 🛠️ Local Development

### 1. Clone the repository
```bash
git clone https://github.com/ABHISHEK120906/Project_Alpha.git
cd Project_Alpha
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-strong-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run migrations & load sample data
```bash
python manage.py migrate
python manage.py seed_demo_data     # Optional: seeds mock clients, projects, tasks
```

### 6. Start the development server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

---

## ☁️ Deployment (Vercel)

1. Push your code to GitHub.
2. Link the repository on [Vercel](https://vercel.com).
3. Set the following environment variables in Vercel Project Settings:
   - `SECRET_KEY`: Production secret key
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.vercel.app`
   - `DATABASE_URL`: Neon PostgreSQL connection string
4. Deployments trigger automatically on push to the `main` branch.

---

## 📄 License
This project is licensed under the MIT License.
