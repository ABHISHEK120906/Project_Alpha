# Freelancer Project Tracker - Development Notes

## Project Information

**Project Name**: Freelancer Project Tracker System
**Purpose**: Production-ready project management system for freelancers
**Tech Stack**: Django, Django REST Framework, Bootstrap 5, Chart.js, SQLite/PostgreSQL

## Setup Instructions

### Environment Setup
- Python 3.14.4
- Virtual environment in `venv/` directory
- Requirements defined in `requirements.txt`

### Common Commands

**Development Server:**
```bash
python manage.py runserver
```

**Migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Create Superuser:**
```bash
python manage.py createsuperuser
```

**Collect Static Files:**
```bash
python manage.py collectstatic
```

## Dependencies Notes

- **Django 6.0.7**: Main web framework
- **Django REST Framework 3.17.1**: API support
- **reportlab 5.0.0**: PDF generation
- **openpyxl 3.1.5**: Excel export
- **django-cors-headers 4.9.0**: CORS support for frontend
- **python-decouple 3.8**: Environment variable management

**Note**: Pillow is excluded from requirements.txt due to Python 3.14 compatibility issues. Use system Pillow (12.2.0) if needed.

## Project Structure

```
freelancer_tracker/
├── core/                      # Main Django app
├── freelancer_tracker/       # Django project settings
├── static/                   # Global static files (css, js, images)
├── templates/                # Global templates
├── media/                    # User uploaded files
├── venv/                     # Virtual environment
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Configuration

### Database
- Development: SQLite
- Production: PostgreSQL (migrate psycopg2-binary when ready)

### Static Files
- Global static: `static/`
- App static: `core/static/`
- Static root: `staticfiles/` (for production)

### Media Files
- Upload directory: `media/`

### Authentication
- Login URL: `login`
- Login redirect: `dashboard`
- Logout redirect: `login`

## Development Phases

1. ✅ Phase 1: Project Setup
2. ✅ Phase 2: Database Design
3. ✅ Phase 3: Backend Development
4. ✅ Phase 4: Frontend Development (Modern UI, responsive sidebar, toast notifications, dark mode)
5. ✅ Phase 5: Dashboard (KPI cards, stat counters, Chart.js graphs, upcoming deadlines, activity feed)
6. ✅ Phase 6: Project Features (Full CRUD for Clients, Projects, Payments, Tasks, Notes & Audit Log)
7. ✅ Phase 7: Reports (ReportLab PDF generation, openpyxl Excel export, monthly summaries)
8. ✅ Phase 8: Security (Strict user data isolation, login_required decorators, CSRF & XSS protection)
9. ⏳ Phase 9: Deployment

## Database Models

### Models Created in Phase 2:
- **Client**: Stores client information (name, email, company, status, etc.)
- **Project**: Tracks projects with status, priority, deadlines, budget, progress
- **Payment**: Tracks payments with status, methods, due dates, invoice numbers
- **Task**: Manages project tasks with status, priority, time tracking
- **Note**: Flexible notes system for projects and clients
- **ActivityLog**: Audit trail for all user actions

### Key Features:
- UUID primary keys for all models
- Foreign key relationships to User for data isolation
- Comprehensive status and priority choices
- Built-in methods for common queries (totals, counts, overdue checks)
- Django admin integration with custom fieldsets and display options
- Full migration support applied successfully

## Backend Development (Phase 3)

### Forms Created:
- **ClientForm**: Client creation/update with validation
- **ProjectForm**: Project creation/update with budget and progress validation
- **PaymentForm**: Payment creation/update with amount validation
- **TaskForm**: Task creation/update with time tracking validation
- **NoteForm**: Note creation/update with project/client relationship validation
- **SearchForm**: Generic search form for filtering records

### Views Implemented:
- **Authentication**: home, register, custom_login, custom_logout
- **Dashboard**: Statistics, upcoming deadlines, recent activities
- **Client CRUD**: list, detail, create, update, delete with search/filter
- **Project CRUD**: list, detail, create, update, delete with search/filter
- **Payment CRUD**: list, detail, create, update, delete with search/filter
- **Task CRUD**: list, detail, create, update, delete with search/filter
- **Note CRUD**: list, detail, create, update, delete with search
- **Activity Log**: List view with pagination

### Key Features:
- Activity logging for all CRUD operations
- Search and filter functionality
- Pagination for large datasets
- User data isolation (users only see their own data)
- Form validation with custom error handling
- Overdue detection for projects, tasks, and payments
- Statistical calculations for dashboard
- IP address tracking for activity logs

### URL Configuration:
- Core app URLs with namespacing
- Django authentication URLs integration
- Static and media file serving
- RESTful URL patterns for all resources
