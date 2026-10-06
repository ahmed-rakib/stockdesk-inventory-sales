import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from .db import get_db
from .models import LoginSession, User, utcnow

COOKIE = 'stockdesk_session'

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 310000).hex()
    return f'pbkdf2_sha256$310000${salt}${digest}'

def check_password(password, encoded):
    _, iterations, salt, expected = encoded.split('$')
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(actual, expected)

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def current_user(request: Request, db=Depends(get_db, scope='function')):
    token = request.cookies.get(COOKIE, '')
    session = db.get(LoginSession, token_hash(token))
    if not session or session.expires_at <= utcnow():
        raise HTTPException(401, 'Please sign in to continue.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if not hmac.compare_digest(request.headers.get('X-CSRF-Token', ''), session.csrf_token):
            raise HTTPException(403, 'Security token expired. Refresh the page and try again.')
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, 'Account not found.')
    return user

def admin_user(user=Depends(current_user)):
    if user.role != 'admin':
        raise HTTPException(403, 'Administrator permission required.')
    return user

