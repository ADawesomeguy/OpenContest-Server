from secrets import token_hex
from hashlib import pbkdf2_hmac
from requests import post


# TODO: Periodically clear out unused tokens
tokens = {}  # Create tokens object


def hash(password, salt):
    """Hash password with salt"""

    return salt + pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


def make_token(username, server):
    """Create and return a token"""

    token = token_hex(32)
    for s in server.split(':'):
        if s != '':
            post('https://' + s, json={'type': 'authorize', 'username': username, 'token': token})
    return token


def save_token(username, token):
    """Save token"""

    if username not in tokens:
        tokens[username] = set()
    tokens[username].add(token)


def check_token(username, token):
    """Check if a token is valid"""
    
    if username in tokens and token in tokens[username]:
        tokens[username].remove(token)
        return True
    return False
