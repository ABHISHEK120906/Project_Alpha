import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancer_tracker.settings')

application = get_wsgi_application()
app = application

# Run database migrations safely on Vercel startup if using SQLite fallback
if os.environ.get('VERCEL'):
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)
    except Exception as e:
        print(f"Vercel auto-migration status: {e}")

