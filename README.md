# FreelanceTrack — Project Tracker

A production-ready freelance project management system built with Django.

---

## Requirements

- Python **3.14+**
- pip

---

## Setup & Run

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Project_Alpha
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open your browser and go to: **http://127.0.0.1:8000**

---

## Common Commands

| Task | Command |
|---|---|
| Start server | `python manage.py runserver` |
| Make migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Create superuser | `python manage.py createsuperuser` |
| Collect static files | `python manage.py collectstatic` |
| Open Django shell | `python manage.py shell` |

---

## Access Points

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Landing page |
| `http://127.0.0.1:8000/login/` | Login |
| `http://127.0.0.1:8000/register/` | Register |
| `http://127.0.0.1:8000/dashboard/` | Main dashboard (login required) |
| `http://127.0.0.1:8000/admin/` | Django admin panel |

---

## Environment Variables (Optional)

Create a `.env` file in the project root to override defaults:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=                        # Leave blank to use SQLite (default)
```

---

## Resetting the Database

```bash
# Delete the SQLite file and re-migrate
del db.sqlite3          # Windows
python manage.py migrate
python manage.py createsuperuser
```

---

## Tech Stack

- **Backend** — Django 6 + Django REST Framework
- **Database** — SQLite (dev) / PostgreSQL (prod)
- **Frontend** — Bootstrap 5, Chart.js, Font Awesome
- **Reports** — ReportLab (PDF), openpyxl (Excel)
