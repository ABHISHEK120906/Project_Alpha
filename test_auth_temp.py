import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancer_tracker.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

c = Client()
results = []

# Test 1: Registration
resp = c.post('/register/', {
    'full_name': 'Test User',
    'email': 'testuser123@example.com',
    'password1': 'TestPass@123',
    'password2': 'TestPass@123',
}, follow=True)
user = User.objects.filter(email='testuser123@example.com').first()
if user and user.is_active:
    results.append('TEST 1 -- Registration: PASS (user created, is_active=True, username=' + user.username + ')')
else:
    results.append('TEST 1 -- Registration: FAIL (user not found or not active)')

# Test 2: Duplicate email
resp2 = c.post('/register/', {
    'full_name': 'Another User',
    'email': 'testuser123@example.com',
    'password1': 'AnotherPass@456',
    'password2': 'AnotherPass@456',
})
count = User.objects.filter(email='testuser123@example.com').count()
if count == 1 and resp2.status_code == 200:
    results.append('TEST 2 -- Duplicate Email: PASS (no duplicate created)')
else:
    results.append('TEST 2 -- Duplicate Email: FAIL (count=' + str(count) + ')')

# Test 3: User login
if user:
    resp3 = c.post('/login/', {
        'login_type': 'user',
        'username': user.username,
        'password': 'TestPass@123',
    }, follow=True)
    if resp3.status_code == 200 and resp3.redirect_chain and '/dashboard/' in resp3.redirect_chain[-1][0]:
        results.append('TEST 3 -- User Login: PASS (redirected to dashboard)')
    else:
        results.append('TEST 3 -- User Login: FAIL (status=' + str(resp3.status_code) + ' chain=' + str(resp3.redirect_chain) + ')')
else:
    results.append('TEST 3 -- User Login: SKIP (no user from Test 1)')

# Test 4: Wrong password
c2 = Client()
resp4 = c2.post('/login/', {
    'login_type': 'user',
    'username': user.username if user else 'testuser123',
    'password': 'WrongPassword',
}, follow=True)
stayed_on_login = (not resp4.redirect_chain or 'login' in str(resp4.redirect_chain))
if stayed_on_login and b'Invalid' in resp4.content:
    results.append('TEST 4 -- Wrong Password: PASS (error message shown)')
elif stayed_on_login:
    results.append('TEST 4 -- Wrong Password: PASS (stayed on login page)')
else:
    results.append('TEST 4 -- Wrong Password: FAIL')

# Test 5: Logout
resp5 = c.post('/logout/', follow=True)
if '/login/' in str(resp5.redirect_chain):
    results.append('TEST 5 -- Logout: PASS (redirected to login)')
else:
    results.append('TEST 5 -- Logout: FAIL (chain=' + str(resp5.redirect_chain) + ')')

# Test 6: Non-admin blocked from admin login
c3 = Client()
resp6 = c3.post('/login/', {
    'login_type': 'admin',
    'username': user.username if user else 'testuser123',
    'password': 'TestPass@123',
}, follow=True)
if b'Access denied' in resp6.content or b'do not have' in resp6.content:
    results.append('TEST 6 -- Admin Login Restriction: PASS (non-admin blocked)')
else:
    snippet = resp6.content[:300]
    results.append('TEST 6 -- Admin Login Restriction: FAIL (content=' + repr(snippet) + ')')

# Test 7: Normal user cannot access admin pages
c4 = Client()
c4.post('/login/', {'login_type': 'user', 'username': user.username if user else 'testuser123', 'password': 'TestPass@123'})
resp7 = c4.get('/admin-dashboard/', follow=True)
content_lower = resp7.content.lower()
if b'forbidden' in content_lower or b'403' in content_lower or b'permission' in content_lower:
    results.append('TEST 7 -- Admin Page Protection: PASS (normal user blocked)')
else:
    results.append('TEST 7 -- Admin Page Protection: FAIL (status=' + str(resp7.status_code) + ')')

# Test 8: No Brevo/OAuth in views
try:
    from core import views as vw
    has_brevo = hasattr(vw, 'send_brevo_welcome_email')
    has_email_service = hasattr(vw, 'send_verification_email')
    has_login_alert = hasattr(vw, 'send_login_alert_email')
    has_verify_view = hasattr(vw, 'verify_email')
    has_resend_view = hasattr(vw, 'resend_verification')
    all_clean = not any([has_brevo, has_email_service, has_login_alert, has_verify_view, has_resend_view])
    if all_clean:
        results.append('TEST 8 -- No Brevo/OAuth Leftovers: PASS (all email/social code removed)')
    else:
        details = []
        if has_brevo: details.append('send_brevo_welcome_email')
        if has_email_service: details.append('send_verification_email')
        if has_login_alert: details.append('send_login_alert_email')
        if has_verify_view: details.append('verify_email view')
        if has_resend_view: details.append('resend_verification view')
        results.append('TEST 8 -- No Brevo/OAuth Leftovers: FAIL (still has: ' + ', '.join(details) + ')')
except Exception as e:
    results.append('TEST 8 -- No Brevo/OAuth Leftovers: FAIL (import error: ' + str(e) + ')')

print('')
for r in results:
    print(r)
print('')
passed = sum(1 for r in results if 'PASS' in r)
print('SUMMARY: ' + str(passed) + '/' + str(len(results)) + ' tests passed')
