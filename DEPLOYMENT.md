# Deployment Guide — FreelanceTrack

## Prerequisites
- Python 3.11+
- Git
- GitHub account
- Render account (free) — for backend
- Vercel account (free) — for static frontend (optional)

---

## Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/freelancer-tracker.git
cd freelancer-tracker

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (copy from .env.example)
cp .env.example .env
# Edit .env with your values

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Start development server
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

---

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-very-long-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=  # Leave empty for SQLite
```

For production, set:
```env
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
SECRET_KEY=<generate a new secure key>
```

---

## Deploying to Render (Backend)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial production deployment"
   git push origin main
   ```

2. **Create a new Web Service on Render**:
   - Go to https://render.com → New → Web Service
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Set Environment Variables** in Render dashboard:
   - `SECRET_KEY` — generate a new key at https://djecrety.ir
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `your-app-name.onrender.com`

4. **Deploy!** Render will:
   - Install dependencies
   - Run `collectstatic`
   - Run `migrate`
   - Start gunicorn

5. **Create superuser** (via Render Shell):
   ```bash
   python manage.py createsuperuser
   ```

---

## Deploying to Vercel (Alternative/Static)

Vercel works best for the frontend static assets. For full Django support, use Render above.

For a hybrid setup:
1. Push the repo to GitHub
2. Go to https://vercel.com → New Project → Import your repo
3. Set `DJANGO_SETTINGS_MODULE = freelancer_tracker.settings`

---

## Migrating to PostgreSQL

1. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary dj-database-url
   ```

2. Update `requirements.txt` (uncomment psycopg2 lines)

3. Set `DATABASE_URL` environment variable:
   ```env
   DATABASE_URL=postgres://user:password@host:5432/dbname
   ```

4. On Render: Add a PostgreSQL database and copy the connection string.

---

## Git Workflow

```bash
git add .
git commit -m "feat: describe your change"
git push origin main
```

Render auto-deploys on every push to `main`.

---

## Folder Structure

```
freelancer_tracker/           # Django project settings
├── settings.py
├── urls.py
└── wsgi.py
core/                         # Main Django app
├── models.py                 # Database models
├── views.py                  # All views (CRUD + Reports + Settings)
├── urls.py                   # URL routing
├── forms.py                  # Form classes
├── admin.py                  # Admin configuration
└── tests.py                  # Unit tests
static/                       # Global static files
├── css/custom.css            # Premium custom styles
└── js/main.js                # Dark mode, toasts, animations
templates/                    # All HTML templates
├── base.html                 # Main layout template
├── dashboard.html            # Dashboard with Chart.js
├── clients/                  # Client CRUD templates
├── projects/                 # Project CRUD templates
├── payments/                 # Payment CRUD templates
├── tasks/                    # Task CRUD templates
├── notes/                    # Note CRUD templates
├── activities/               # Activity log template
├── reports/                  # Reports + export template
├── registration/             # Login & Register
└── settings.html             # User settings
Procfile                      # Gunicorn command for Render
render.yaml                   # Render deployment config
requirements.txt              # Python dependencies
manage.py                     # Django management script
```
