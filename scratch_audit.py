import os
import sys
import ast
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancer_tracker.settings')
import django
django.setup()

from django.template import loader, TemplateSyntaxError
from django.urls import get_resolver, reverse, NoReverseMatch
from django.apps import apps
from django.db import models
from django.conf import settings

def audit_templates():
    print("=== AUDITING TEMPLATES ===")
    template_dirs = [
        os.path.join(settings.BASE_DIR, 'templates'),
        os.path.join(settings.BASE_DIR, 'core', 'templates')
    ]
    template_errors = []
    template_count = 0
    for t_dir in template_dirs:
        if not os.path.exists(t_dir):
            continue
        for root, dirs, files in os.walk(t_dir):
            for f in files:
                if f.endswith(('.html', '.txt')):
                    template_count += 1
                    full_path = os.path.join(root, f)
                    rel_to_templates = os.path.relpath(full_path, t_dir).replace('\\', '/')
                    try:
                        # Try loading with Django template engine
                        loader.get_template(rel_to_templates)
                    except Exception as e:
                        template_errors.append(f"[TEMPLATE ERROR] {rel_to_templates} ({full_path}): {e}")
    print(f"Checked {template_count} templates. Found {len(template_errors)} errors.")
    for err in template_errors:
        print("  -", err)

def audit_models_and_signals():
    print("\n=== AUDITING MODELS, SIGNALS, & SAVE OVERRIDES ===")
    for model in apps.get_models():
        model_name = f"{model._meta.app_label}.{model.__name__}"
        # Check custom save methods
        save_func = getattr(model, 'save', None)
        has_custom_save = save_func and save_func != models.Model.save
        
        # Check cascade rules
        cascades = []
        for field in model._meta.get_fields():
            if hasattr(field, 'remote_field') and field.remote_field:
                on_delete = getattr(field.remote_field, 'on_delete', None)
                if on_delete == models.CASCADE:
                    cascades.append((field.name, field.related_model.__name__ if field.related_model else 'None'))
        
        print(f"Model: {model_name} | Custom save: {has_custom_save} | Cascades on delete: {cascades}")

def audit_middlewares():
    print("\n=== AUDITING MIDDLEWARES ===")
    for mw in settings.MIDDLEWARE:
        print(f"  - {mw}")

def audit_urls():
    print("\n=== AUDITING URLS ===")
    resolver = get_resolver()
    url_patterns = resolver.url_patterns
    print(f"Top-level URL patterns: {len(url_patterns)}")

if __name__ == '__main__':
    audit_templates()
    audit_models_and_signals()
    audit_middlewares()
    audit_urls()
