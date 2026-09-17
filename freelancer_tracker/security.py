"""
FreelanceTrack — Security Utilities
====================================
A collection of security helpers used across the application.

Includes:
- sanitize_filename:   Safe filename generation for media uploads
- validate_file_upload: File type and size validation
- generate_secure_token: Cryptographically secure token generation
- is_safe_redirect_url: SSRF-safe redirect URL validation
"""

import hashlib
import hmac
import os
import re
import secrets
import string
import unicodedata
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest

# ── File upload constants ─────────────────────────────────────────────────────

#: Allowed MIME types → max file size in bytes
ALLOWED_UPLOAD_TYPES: dict[str, int] = {
    # Images
    'image/jpeg':   5 * 1024 * 1024,   # 5 MB
    'image/png':    5 * 1024 * 1024,
    'image/gif':    3 * 1024 * 1024,
    'image/webp':   5 * 1024 * 1024,
    # Documents
    'application/pdf':  10 * 1024 * 1024,  # 10 MB
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 10 * 1024 * 1024,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':       10 * 1024 * 1024,
    'text/plain':   2 * 1024 * 1024,    # 2 MB
}

#: Extension allowlist — must match ALLOWED_UPLOAD_TYPES
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.pdf', '.docx', '.xlsx', '.txt',
})

#: Dangerous extensions that must always be blocked
BLOCKED_EXTENSIONS: frozenset[str] = frozenset({
    '.php', '.phtml', '.php3', '.php4', '.php5', '.phar',
    '.exe', '.bat', '.cmd', '.sh', '.bash', '.ps1',
    '.py', '.rb', '.pl', '.cgi',
    '.js', '.vbs', '.jar',
    '.svg',   # SVG can contain embedded JS
    '.html', '.htm', '.xhtml',
})


# ── Token constants ───────────────────────────────────────────────────────────

TOKEN_ALPHABET = string.ascii_letters + string.digits
DEFAULT_TOKEN_LENGTH = 64


# ─────────────────────────────────────────────────────────────────────────────
# Filename Sanitization
# ─────────────────────────────────────────────────────────────────────────────

def sanitize_filename(filename: str) -> str:
    """
    Return a safe version of *filename* suitable for use as a filesystem path.

    Steps:
    1. Normalise Unicode (NFKD) and encode to ASCII, dropping non-ASCII chars.
    2. Replace whitespace and path-separator characters with underscores.
    3. Strip leading dots to prevent hidden-file tricks.
    4. Collapse consecutive underscores/hyphens.
    5. Truncate the stem to 100 characters (keeping the extension).

    The returned name is always non-empty.  If the sanitised stem is empty the
    function returns a random hex token with the original extension.

    Example::

        >>> sanitize_filename("../../../etc/passwd")
        'etc_passwd'
        >>> sanitize_filename("Rëport (Final) v2.pdf")
        'Rport_Final_v2.pdf'
    """
    # NFKD normalise and strip non-ASCII
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')

    path = Path(filename)
    stem = path.stem
    suffix = path.suffix.lower()

    # Replace dangerous characters
    stem = re.sub(r'[\s/\\:*?"<>|]+', '_', stem)
    # Remove leading dots (hidden-file trick)
    stem = stem.lstrip('.')
    # Collapse repeated separators
    stem = re.sub(r'[_\-]{2,}', '_', stem).strip('_')
    # Truncate
    stem = stem[:100]

    if not stem:
        stem = secrets.token_hex(8)

    return f"{stem}{suffix}" if suffix else stem


# ─────────────────────────────────────────────────────────────────────────────
# File Upload Validation
# ─────────────────────────────────────────────────────────────────────────────

class FileUploadError(ValueError):
    """Raised when an uploaded file fails security validation."""


def validate_file_upload(
    uploaded_file,
    *,
    allowed_types: dict[str, int] | None = None,
    allowed_extensions: frozenset[str] | None = None,
) -> None:
    """
    Validate an uploaded file's extension, MIME type, and size.

    Args:
        uploaded_file: A Django ``InMemoryUploadedFile`` / ``TemporaryUploadedFile``.
        allowed_types:  Override the default ``ALLOWED_UPLOAD_TYPES`` dict.
        allowed_extensions: Override the default ``ALLOWED_EXTENSIONS`` set.

    Raises:
        FileUploadError: If the file fails any validation check.
    """
    if allowed_types is None:
        allowed_types = ALLOWED_UPLOAD_TYPES
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS

    # ── Extension check ───────────────────────────────────────────────────────
    ext = Path(uploaded_file.name).suffix.lower()

    if ext in BLOCKED_EXTENSIONS:
        raise FileUploadError(
            f"File type '{ext}' is not permitted for security reasons."
        )

    if ext not in allowed_extensions:
        allowed = ', '.join(sorted(allowed_extensions))
        raise FileUploadError(
            f"File extension '{ext}' is not allowed. Permitted: {allowed}"
        )

    # ── MIME type check ───────────────────────────────────────────────────────
    content_type = getattr(uploaded_file, 'content_type', '').split(';')[0].strip()
    if content_type not in allowed_types:
        raise FileUploadError(
            f"File content type '{content_type}' is not allowed."
        )

    # ── Size check ────────────────────────────────────────────────────────────
    max_size = allowed_types[content_type]
    if uploaded_file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = uploaded_file.size / (1024 * 1024)
        raise FileUploadError(
            f"File size {actual_mb:.1f} MB exceeds the maximum allowed {max_mb:.0f} MB "
            f"for content type '{content_type}'."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Secure Token Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_secure_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
    """
    Generate a cryptographically secure URL-safe token.

    Uses ``secrets.choice`` over a restricted alphabet (letters + digits) to
    avoid URL-encoding issues with base64-style tokens.

    Args:
        length: Number of characters in the token (default: 64).

    Returns:
        A random alphanumeric token of exactly *length* characters.
    """
    return ''.join(secrets.choice(TOKEN_ALPHABET) for _ in range(length))


def generate_secure_hex_token(nbytes: int = 32) -> str:
    """
    Generate a hex-encoded secure random token (e.g., for HMAC secrets).

    Args:
        nbytes: Number of random bytes (hex string will be 2× longer).

    Returns:
        A hex string of length ``nbytes * 2``.
    """
    return secrets.token_hex(nbytes)


# ─────────────────────────────────────────────────────────────────────────────
# Safe Redirect URL Validation
# ─────────────────────────────────────────────────────────────────────────────

def is_safe_redirect_url(url: str, request: HttpRequest) -> bool:
    """
    Return ``True`` if *url* is safe to redirect to.

    Wraps Django's ``url_has_allowed_host_and_scheme`` with the site's
    ``ALLOWED_HOSTS`` to prevent open-redirect and SSRF vulnerabilities.

    Args:
        url:     The redirect target URL (may be relative or absolute).
        request: The current HTTP request (used to derive allowed hosts).

    Returns:
        ``True`` if the URL is safe, ``False`` otherwise.
    """
    from django.utils.http import url_has_allowed_host_and_scheme
    allowed_hosts = set(getattr(settings, 'ALLOWED_HOSTS', []))
    # Always allow relative URLs (same-origin)
    allowed_hosts.add(request.get_host())
    return url_has_allowed_host_and_scheme(
        url=url,
        allowed_hosts=allowed_hosts,
        require_https=not getattr(settings, 'DEBUG', True),
    )


# ─────────────────────────────────────────────────────────────────────────────
# HMAC Signature Helpers (e.g., webhook verification)
# ─────────────────────────────────────────────────────────────────────────────

def compute_hmac_sha256(secret: str, payload: str) -> str:
    """
    Compute an HMAC-SHA256 signature for *payload* using *secret*.

    Used for signing and verifying webhook payloads or internal API tokens.

    Args:
        secret:  The shared secret key (UTF-8 string).
        payload: The message to sign (UTF-8 string).

    Returns:
        Lowercase hex HMAC-SHA256 digest.
    """
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def verify_hmac_sha256(secret: str, payload: str, signature: str) -> bool:
    """
    Verify an HMAC-SHA256 signature in constant time (prevents timing attacks).

    Args:
        secret:    The shared secret key.
        payload:   The original message.
        signature: The hex digest to verify against.

    Returns:
        ``True`` if *signature* matches, ``False`` otherwise.
    """
    expected = compute_hmac_sha256(secret, payload)
    return hmac.compare_digest(expected, signature.lower())
