from hashlib import pbkdf2_hmac
from requests import post


tokens = {}  # Create tokens object


def hash(password, salt):
    """Hash password with salt"""

    return salt + pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


def authorize_request(username, homeserver, token):
    """Request an authorization"""

    return post('https://' + homeserver, json={'type': 'authorize', 'username': username, 'token': token}).status_code
