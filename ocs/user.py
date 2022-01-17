from secrets import token_hex
from hashlib import pbkdf2_hmac
from requests import post


tokens = {}  # Create tokens object


def hash(password, salt):
    """Hash password with salt"""

    return salt + pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


def make_token(username):
    """Create and return a token"""

    token = token_hex(32)
    if username not in tokens:
        tokens[username] = {}
    tokens[username].add(token)
    return token


def check_token(username, token):
    """Check if a token is valid"""
    
    if username in tokens and token in tokens[username]:
        tokens[username].remove(token)
        return True
    return False


def authorize_request(username, homeserver, token):
    """Request an authorization"""

    return post('https://' + homeserver, json={'type': 'authorize', 'username': username, 'token': token}).status_code
