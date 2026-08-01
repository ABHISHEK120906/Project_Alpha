"""
FreelanceTrack — Email Notification Service
Sends responsive HTML emails for Registration Welcome and Security Login Alerts.
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_welcome_email(user, request=None):
    """Sends account registration welcome email to newly created users."""
    user_email = getattr(user, 'email', '')
    username = getattr(user, 'username', 'User')

    # Default login URL fallback
    login_url = request.build_absolute_uri('/login/') if request else 'https://project-alpha-pl18hkv1h-abhisheks120906s-projects.vercel.app/login/'

    subject = 'Welcome to FreelanceTrack! 🚀'
    context = {
        'username': username,
        'login_url': login_url,
    }

    try:
        html_content = render_to_string('emails/email_welcome.html', context)
        text_content = strip_tags(html_content)

        recipient_list = [user_email] if user_email else []
        if not recipient_list:
            logger.info(f"Welcome email skipped for {username}: No email address provided.")
            return False

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'FreelanceTrack <no-reply@freelancetrack.com>'),
            to=recipient_list
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
        logger.info(f"Welcome email successfully sent to {user_email}")
        return True
    except Exception as e:
        logger.warning(f"Could not send welcome email to {user_email}: {e}")
        return False


def send_login_alert_email(user, request=None):
    """Sends security notification email upon user login."""
    user_email = getattr(user, 'email', '')
    username = getattr(user, 'username', 'User')

    client_ip = '127.0.0.1'
    user_agent = 'Unknown Device'

    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Device')

    login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p %Z')
    subject = '🔐 Security Alert: New Login to FreelanceTrack'

    context = {
        'username': username,
        'login_time': login_time,
        'client_ip': client_ip,
        'user_agent': user_agent,
    }

    try:
        html_content = render_to_string('emails/email_login_alert.html', context)
        text_content = strip_tags(html_content)

        recipient_list = [user_email] if user_email else []
        if not recipient_list:
            logger.info(f"Login alert email skipped for {username}: No email address on profile.")
            return False

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'FreelanceTrack <no-reply@freelancetrack.com>'),
            to=recipient_list
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
        logger.info(f"Login security alert email sent to {user_email}")
        return True
    except Exception as e:
        logger.warning(f"Could not send login security alert email: {e}")
        return False
