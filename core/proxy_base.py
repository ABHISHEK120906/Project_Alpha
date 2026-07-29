"""
FreelanceTrack — External API Proxy Base Class
Provides a secure architecture for proxying third-party API requests.
Ensures the frontend never directly accesses third-party URLs or holds credentials.
"""

import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class ExternalAPIProxyException(Exception):
    """Custom exception for backend proxy failures."""
    pass


class ExternalAPIProxy:
    """
    Abstract Base Class for calling external third-party APIs from Django.
    
    Mandatory Rules Enforced:
    1. Frontend NEVER talks to external APIs directly.
    2. API Keys stored ONLY in backend environment variables.
    3. Input parameters validated and sanitized.
    4. Allowed domain whitelisting (SSRF protection).
    5. Response filtered to return minimum required data to frontend.
    """

    ALLOWED_DOMAINS = []  # Subclasses must define allowed hostnames e.g. ['api.github.com']
    TIMEOUT_SECONDS = 10

    def get_api_key(self):
        """Override in subclass to retrieve specific key from settings/environment."""
        raise NotImplementedError("Subclasses must implement get_api_key()")

    def sanitize_input(self, data):
        """Sanitize query parameters or json payloads before sending upstream."""
        if isinstance(data, dict):
            return {k: str(v).strip() for k, v in data.items() if v is not None}
        return data

    def validate_url(self, target_url):
        """Enforces domain whitelist to prevent SSRF vulnerabilities."""
        parsed = urllib.parse.urlparse(target_url)
        if parsed.scheme not in ['http', 'https']:
            raise ExternalAPIProxyException("Only HTTP and HTTPS protocols are permitted.")
        
        domain = parsed.netloc.split(':')[0]
        if domain not in self.ALLOWED_DOMAINS:
            logger.warning(f"Blocked unauthorized proxy attempt to domain: {domain}")
            raise ExternalAPIProxyException(f"Domain '{domain}' is not in the proxy whitelist.")

    def filter_response_data(self, raw_data):
        """
        Override in subclass to strip sensitive fields (tokens, internal IDs, debug info)
        before returning to frontend.
        """
        return raw_data

    def make_request(self, target_url, method='GET', params=None, body=None, headers=None):
        """
        Executes outbound HTTPS request safely.
        Applies headers, API keys, timeout, and response filtering.
        """
        self.validate_url(target_url)

        # Build URL with sanitized query params
        if params:
            sanitized_params = self.sanitize_input(params)
            query_string = urllib.parse.urlencode(sanitized_params)
            target_url = f"{target_url}?{query_string}"

        req_headers = headers or {}
        req_headers['User-Agent'] = 'FreelanceTrack-Proxy/1.0'
        
        # Inject API Key from backend environment safely
        api_key = self.get_api_key()
        if api_key:
            req_headers['Authorization'] = f"Bearer {api_key}"

        encoded_body = None
        if body:
            sanitized_body = self.sanitize_input(body)
            encoded_body = json.dumps(sanitized_body).encode('utf-8')
            req_headers['Content-Type'] = 'application/json'

        req = urllib.request.Request(target_url, data=encoded_body, headers=req_headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as response:
                content_type = response.headers.get('Content-Type', '')
                raw_bytes = response.read()
                
                if 'application/json' in content_type:
                    parsed_json = json.loads(raw_bytes.decode('utf-8'))
                    filtered_data = self.filter_response_data(parsed_json)
                    return Response(filtered_data, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Success"}, status=status.HTTP_200_OK)

        except urllib.error.HTTPError as e:
            logger.error(f"External API Error ({e.code}): {e.reason}")
            return Response(
                {"error": "Upstream API error", "status": e.code},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except urllib.error.URLError as e:
            logger.error(f"Proxy Connection Failure: {e.reason}")
            return Response(
                {"error": "Failed to reach external service"},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Proxy Internal Exception: {str(e)}")
            return Response(
                {"error": "Internal proxy error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
