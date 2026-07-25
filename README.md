# Freelancer Project Tracker System

A production-ready project management system for freelancers to track clients, projects, payments, tasks, and generate reports.

## Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript (ES6)
- Bootstrap 5
- Chart.js
- Font Awesome

### Backend
- Python
- Django
- Django REST Framework

### Database
- SQLite (Development)
- PostgreSQL (Production - Easy migration support)

### Authentication
- Django Authentication (Login, Logout, Registration, Password Hashing)

### Deployment
- Frontend: Vercel
- Backend: Render
- Database: SQLite (later PostgreSQL)

## Project Structure

```
freelancer_tracker/
├── core/                      # Main Django app
│   ├── migrations/           # Database migrations
│   ├── static/               # Static files (CSS, JS, images)
│   ├── templates/            # HTML templates
│   ├── admin.py              # Admin configuration
│   ├── apps.py               # App configuration
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── urls.py               # URL routing
│   └── tests.py              # Unit tests
├── freelancer_tracker/       # Django project settings
│   ├── settings.py           # Project settings
│   ├── urls.py               # Main URL configuration
│   └── wsgi.py               # WSGI configuration
├── static/                   # Global static files
│   ├── css/                  # Custom CSS
│   ├── js/                   # Custom JavaScript
│   └── images/               # Images and assets
├── templates/                # Global templates
├── venv/                     # Virtual environment
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Development Phases

- **Phase 1**: Project Setup ✓
- **Phase 2**: Database Design
- **Phase 3**: Backend Development
- **Phase 4**: Frontend Development
- **Phase 5**: Dashboard
- **Phase 6**: Project Features
- **Phase 7**: Reports
- **Phase 8**: Security
- **Phase 9**: Deployment

## Features

- Client Management
- Project Tracking
- Deadline Management
- Payment Tracking
- Task Management
- Notes & Activity Logging
- Interactive Dashboard with Charts
- Advanced Reports (PDF/Excel export)
- Search, Filter, Sorting, Pagination
- Dark Mode
- Responsive Design

## License

MIT License
