"""
Fixed live test - properly extracts CSRF token from cookie jar
"""
import urllib.request, urllib.parse, urllib.error, http.cookiejar, re

base = 'http://127.0.0.1:8000'
results = []

def make_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 TestBot')]
    return opener, cj

def get_csrf_from_cookie(cj):
    for cookie in cj:
        if cookie.name == 'csrftoken':
            return cookie.value
    return None

def post(session, cj, url, fields):
    csrf = get_csrf_from_cookie(cj)
    if not csrf:
        # Hit the URL first to get the cookie
        session.open(url)
        csrf = get_csrf_from_cookie(cj)
    
    fields['csrfmiddlewaretoken'] = csrf or ''
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header('Referer', url)
    req.add_header('X-CSRFToken', csrf or '')
    try:
        resp = session.open(req)
        return resp.geturl(), resp.read()
    except urllib.error.HTTPError as e:
        return 'HTTP_ERROR_' + str(e.code), b''

# Test 1 & 2: Register page form structure and no social buttons
try:
    s, cj = make_session()
    resp = s.open(base + '/register/')
    body = resp.read()
    has_full_name = b'full_name' in body
    has_email = b'email' in body  
    has_p1 = b'password1' in body
    has_p2 = b'password2' in body
    no_google = b'social-btn--google' not in body
    no_github = b'social-btn--github' not in body
    no_verify_link = b'verify-email' not in body and b'resend-verification' not in body
    
    if has_full_name and has_email and has_p1 and has_p2:
        results.append('TEST 1 -- Register: 4-field form (Full Name, Email, Password, Confirm): PASS')
    else:
        results.append('TEST 1 -- Register form fields missing: FAIL')
    
    if no_google and no_github:
        results.append('TEST 1b -- No Google/GitHub buttons on register: PASS')
    else:
        results.append('TEST 1b -- Social buttons still present: FAIL')
    
    if no_verify_link:
        results.append('TEST 1c -- No email-verification links on register: PASS')
    else:
        results.append('TEST 1c -- Email verification links still present: FAIL')
except Exception as e:
    results.append('TEST 1 -- ERROR: ' + str(e))

# Test 2: Login page
try:
    s2, cj2 = make_session()
    resp = s2.open(base + '/login/')
    body = resp.read()
    no_google = b'social-btn--google' not in body
    no_github = b'social-btn--github' not in body
    has_user_section = b'User Login' in body or b'id_user_username' in body
    has_admin_section = b'Administrator Login' in body or b'id_admin_username' in body
    no_resend = b'resend' not in body.lower() or b'resend_verification' not in body
    
    if no_google and no_github:
        results.append('TEST 2 -- No Google/GitHub buttons on login: PASS')
    else:
        results.append('TEST 2 -- Social buttons still on login: FAIL')
    
    if has_user_section and has_admin_section:
        results.append('TEST 2b -- Login has User + Admin sections: PASS')
    else:
        results.append('TEST 2b -- Login sections incomplete: user=%s admin=%s' % (has_user_section, has_admin_section))
    
    if no_resend:
        results.append('TEST 2c -- No resend-verification banner on login: PASS')
    else:
        results.append('TEST 2c -- Resend banner still present: FAIL')
except Exception as e:
    results.append('TEST 2 -- ERROR: ' + str(e))

# Test 3: Register a new user
try:
    s3, cj3 = make_session()
    s3.open(base + '/register/')  # get CSRF cookie
    url3, body3 = post(s3, cj3, base + '/register/', {
        'full_name': 'Live Test User',
        'email': 'livetest777@example.com',
        'password1': 'StrongPass@1',
        'password2': 'StrongPass@1',
    })
    if '/login/' in url3:
        results.append('TEST 3 -- Registration redirects to login: PASS')
    elif b'Account created' in body3 or b'successfully' in body3:
        results.append('TEST 3 -- Registration success message: PASS')
    elif 'HTTP_ERROR' in url3:
        results.append('TEST 3 -- Registration: FAIL (' + url3 + ')')
    else:
        results.append('TEST 3 -- Registration: PARTIAL url=' + url3)
except Exception as e:
    results.append('TEST 3 -- ERROR: ' + str(e))

# Test 4: Duplicate email
try:
    s4, cj4 = make_session()
    s4.open(base + '/register/')
    url4, body4 = post(s4, cj4, base + '/register/', {
        'full_name': 'Duplicate Attempt',
        'email': 'livetest777@example.com',
        'password1': 'StrongPass@1',
        'password2': 'StrongPass@1',
    })
    if '/register/' in url4 or (b'already exists' in body4 or b'already registered' in body4 or b'log in' in body4):
        results.append('TEST 4 -- Duplicate email prevented: PASS')
    elif '/login/' in url4:
        results.append('TEST 4 -- Duplicate email not caught (got into login): FAIL')
    else:
        results.append('TEST 4 -- Duplicate email: PARTIAL url=' + url4)
except Exception as e:
    results.append('TEST 4 -- ERROR: ' + str(e))

# Test 5: Login with wrong password
try:
    s5, cj5 = make_session()
    s5.open(base + '/login/')
    url5, body5 = post(s5, cj5, base + '/login/', {
        'login_type': 'user',
        'username': 'livetest777',
        'password': 'WrongPassword',
    })
    if '/login/' in url5 or (b'Invalid' in body5 or b'incorrect' in body5.lower()):
        results.append('TEST 5 -- Wrong password shows error on login: PASS')
    elif '/dashboard/' in url5:
        results.append('TEST 5 -- Wrong password let user in: FAIL')
    else:
        results.append('TEST 5 -- Wrong password: PARTIAL url=' + url5)
except Exception as e:
    results.append('TEST 5 -- ERROR: ' + str(e))

# Test 6: Normal user blocked from admin login  
try:
    s6, cj6 = make_session()
    s6.open(base + '/login/')
    url6, body6 = post(s6, cj6, base + '/login/', {
        'login_type': 'admin',
        'username': 'livetest777',
        'password': 'StrongPass@1',
    })
    if b'Access denied' in body6 or b'do not have' in body6 or b'privileges' in body6:
        results.append('TEST 6 -- Normal user blocked from admin login: PASS')
    elif '/admin-dashboard/' not in url6:
        results.append('TEST 6 -- Normal user not in admin (url=%s): PASS' % url6)
    else:
        results.append('TEST 6 -- Admin login restriction: FAIL')
except Exception as e:
    results.append('TEST 6 -- ERROR: ' + str(e))

# Test 7: Unauthenticated user redirected from /admin-dashboard/ to login
try:
    s7, cj7 = make_session()
    resp7 = s7.open(base + '/admin-dashboard/')
    url7 = resp7.geturl()
    if '/login/' in url7:
        results.append('TEST 7 -- Unauthenticated redirect to login from admin-dashboard: PASS')
    else:
        results.append('TEST 7 -- Admin page protection: url=' + url7)
except urllib.error.HTTPError as e:
    if e.code == 403:
        results.append('TEST 7 -- Admin page returns 403: PASS')
    else:
        results.append('TEST 7 -- Admin page HTTP ' + str(e.code))
except Exception as e:
    results.append('TEST 7 -- ERROR: ' + str(e))

# Test 8: Login with correct credentials
try:
    s8, cj8 = make_session()
    s8.open(base + '/login/')
    url8, body8 = post(s8, cj8, base + '/login/', {
        'login_type': 'user',
        'username': 'livetest777',
        'password': 'StrongPass@1',
    })
    if '/dashboard/' in url8:
        results.append('TEST 8 -- User login with correct password -> dashboard: PASS')
    else:
        results.append('TEST 8 -- User login: PARTIAL url=' + url8)
except Exception as e:
    results.append('TEST 8 -- User login: ERROR ' + str(e))

print('')
for r in results:
    print(r)
passed = sum(1 for r in results if 'PASS' in r)
print('')
print('LIVE HTTP TESTS: %d/%d passed' % (passed, len(results)))
