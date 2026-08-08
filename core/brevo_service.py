"""
core/brevo_service.py

Brevo (formerly Sendinblue) Transactional Email & Contact Management Service.
Handles automatic contact creation/updates and transactional email dispatches.
Uses Brevo REST API v3 via standard requests library safely and asynchronously/non-blockingly.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_CONTACTS_API_URL = "https://api.brevo.com/v3/contacts"
BREVO_SMTP_EMAIL_API_URL = "https://api.brevo.com/v3/smtp/email"


def get_brevo_headers():
    """Build request headers containing the Brevo API Key safely from settings."""
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    if not api_key:
        return None
    return {
        "api-key": api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }


def create_or_update_brevo_contact(email: str, first_name: str = '', last_name: str = '', extra_attributes: dict = None) -> bool:
    """
    Creates or updates a contact in Brevo.
    Using updateEnabled=True ensures existing contacts are updated without duplicate errors.
    """
    if not email:
        logger.warning("Brevo contact sync skipped: No email provided.")
        return False

    headers = get_brevo_headers()
    if not headers:
        logger.error("Brevo contact sync failed: BREVO_API_KEY is not configured in settings/environment.")
        return False

    attributes = {}
    if first_name:
        attributes["FIRSTNAME"] = first_name
    if last_name:
        attributes["LASTNAME"] = last_name

    if extra_attributes and isinstance(extra_attributes, dict):
        attributes.update(extra_attributes)

    payload = {
        "email": email.strip().lower(),
        "attributes": attributes,
        "updateEnabled": True,
    }

    try:
        response = requests.post(BREVO_CONTACTS_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201, 204):
            logger.info(f"Successfully created/updated Brevo contact: {email}")
            return True
        else:
            logger.error(f"Failed to create/update Brevo contact ({email}): Status {response.status_code} - {response.text}")
            return False
    except Exception as exc:
        logger.error(f"Exception occurred while contacting Brevo API for contact {email}: {exc}")
        return False


def send_brevo_welcome_email(user, request=None) -> bool:
    """
    Sends Welcome/Registration transactional email using Brevo Transactional Email API.
    Also ensures the user is created/updated as a Brevo contact first.
    Non-blocking: failure to send email will not cause exception propagation.
    """
    email = getattr(user, 'email', '').strip().lower()
    if not email:
        logger.warning("Brevo welcome email skipped: User has no email address.")
        return False

    first_name = (getattr(user, 'first_name', '') or '').strip()
    last_name = (getattr(user, 'last_name', '') or '').strip()
    username = (getattr(user, 'username', '') or '').strip()

    display_first_name = first_name or username or "there"
    full_name = user.get_full_name().strip() if hasattr(user, 'get_full_name') and user.get_full_name() else (first_name or username or "Valued User")

    # 1. Automatically create/update contact in Brevo first
    create_or_update_brevo_contact(email, first_name=first_name, last_name=last_name)

    # 2. Check Brevo API credentials
    headers = get_brevo_headers()
    if not headers:
        logger.error("Brevo transactional email failed: BREVO_API_KEY is missing or invalid.")
        return False

    template_id = getattr(settings, 'BREVO_WELCOME_TEMPLATE_ID', 4)
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', 'abhishekmutthalkar10@gmail.com')
    sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'Freelancing Tracker')

    # Resolve Site URL for CTA link
    if request:
        site_url = request.build_absolute_uri('/')[:-1]
    else:
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')

    payload = {
        "to": [
            {
                "email": email,
                "name": full_name
            }
        ],
        "templateId": int(template_id),
        "params": {
            "firstName": display_first_name,
            "name": full_name,
            "FIRSTNAME": display_first_name,
            "username": username,
            "SITE_URL": site_url,
            "site_url": site_url,
        },
        "sender": {
            "email": sender_email,
            "name": sender_name
        }
    }

    try:
        response = requests.post(BREVO_SMTP_EMAIL_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201, 202):
            logger.info(f"Brevo Welcome transactional email successfully dispatched to {email}")
            return True
        else:
            logger.error(f"Brevo API error sending welcome email to {email}: Status {response.status_code} - {response.text}")
            return False
    except Exception as exc:
        logger.error(f"Network error while sending Brevo welcome email to {email}: {exc}")
        return False
