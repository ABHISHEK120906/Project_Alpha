import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

logger = logging.getLogger(__name__)

ADMIN_NOTIFICATION_EMAIL = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'abhishekmutthalkar121@gmail.com')


def send_verification_email(user, token_obj, request=None):
    """
    Sends email verification link and 6-digit OTP to unverified user.
    Uses Brevo REST API v3 when BREVO_API_KEY is configured.
    Falls back to standard Django EmailBackend if Brevo is unconfigured.
    """
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    if api_key:
        from .brevo_service import send_brevo_verification_email
        return send_brevo_verification_email(user, token_obj, request)

    user_email = getattr(user, 'email', '')
    username = getattr(user, 'username', 'User')

    if request:
        verification_url = request.build_absolute_uri(
            reverse('core:verify_email_token', kwargs={'token': token_obj.token})
        )
    else:
        site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        verification_url = f"{site_url}/verify-email/{token_obj.token}/"

    subject = '✉️ Action Required: Verify your FreelanceTrack email address'
    context = {
        'username': username,
        'verification_url': verification_url,
        'otp': token_obj.otp,
        'expires_at': token_obj.expires_at,
    }

    try:
        html_content = render_to_string('emails/email_verification.html', context)
        text_content = strip_tags(html_content)

        if not user_email:
            logger.warning(f"Verification email failed for {username}: No recipient email address.")
            return False

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'FreelanceTrack <no-reply@freelancetrack.com>'),
            to=[user_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Verification email sent to {user_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user_email}: {e}")
        return False



def send_admin_new_user_notification(user, request=None):
    """
    Sends automated email notification to Super Admin (abhishekmutthalkar121@gmail.com)
    immediately after a user account is verified.
    """
    user_name = user.get_full_name().strip() or user.username
    registered_email = user.email
    reg_datetime = user.date_joined.strftime('%B %d, %Y at %I:%M %p %Z')

    subject = f"🔔 New Account Verified: {user_name} ({registered_email})"
    context = {
        'user_name': user_name,
        'username': user.username,
        'registered_email': registered_email,
        'registration_datetime': reg_datetime,
        'account_type': 'User',
        'status': 'Verified',
    }

    try:
        html_content = render_to_string('emails/email_admin_notification.html', context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'FreelanceTrack <no-reply@freelancetrack.com>'),
            to=[ADMIN_NOTIFICATION_EMAIL]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Admin notification email sent to {ADMIN_NOTIFICATION_EMAIL} for user {registered_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification email to {ADMIN_NOTIFICATION_EMAIL}: {e}")
        return False


def send_welcome_email(user, request=None):
    """
    Sends welcome email to user.
    If BREVO_API_KEY is configured, sends via Brevo Transactional Email API (creating/updating Brevo contact first).
    Falls back to standard Django Email Backend if Brevo is unconfigured or fails.
    """
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    if api_key:
        from .brevo_service import send_brevo_welcome_email
        success = send_brevo_welcome_email(user, request)
        if success:
            return True

    user_email = getattr(user, 'email', '')
    username = getattr(user, 'username', 'User')

    login_url = request.build_absolute_uri('/login/') if request else '/login/'

    subject = 'Welcome to FreelanceTrack! 🚀'
    context = {
        'username': username,
        'login_url': login_url,
        'support_email': 'support@freelancetrack.com',
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
        msg.send(fail_silently=False)
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
