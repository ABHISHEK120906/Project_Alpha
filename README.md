# FreelanceTrack — Freelancer Project Management System

A production-ready project management system built for freelancers.
Track clients, projects, payments, tasks, and generate reports — all in one place.

## Tech Stack

- **Backend**: Django 6.0.7 + Django REST Framework
- **Database**: PostgreSQL (Neon) via `dj-database-url`
- **Static Files**: WhiteNoise
- **Deployment**: Vercel (Serverless Python)
- **Reports**: ReportLab (PDF) + openpyxl (Excel)

## Features

- 🔐 User authentication with full data isolation
- 👥 Client management (CRUD)
- 📁 Project tracking with status, priority & deadlines
- 💳 Payment tracking with invoice numbers
- ✅ Task management with time tracking
- 📝 Notes system for projects & clients
- 📊 Dashboard with Chart.js analytics
- 📄 PDF & Excel report exports
- 🌙 Dark mode support
- 🔍 Activity audit log

## Local Development

```bash
# 1. Clone the repo
git clone https://github.com/ABHISHEK120906/Project_Alpha.git
cd Project_Alpha

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
# Copy the values below and fill in your own:
#   SECRET_KEY=your-secret-key
#   DEBUG=True
#   ALLOWED_HOSTS=localhost,127.0.0.1
#   DATABASE_URL=postgresql://...  (Neon DB connection string)

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver
```

Open http://127.0.0.1:8000

## Vercel Deployment

1. Push to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import repo
3. Add these **Environment Variables** in Vercel dashboard:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Your Django secret key |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app.vercel.app` |
| `DATABASE_URL` | Neon PostgreSQL connection string |

4. Vercel auto-deploys on every push to `main`

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key (keep private!) |
| `DEBUG` | `True` for dev, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed domains |
| `DATABASE_URL` | Neon PostgreSQL connection URL |
