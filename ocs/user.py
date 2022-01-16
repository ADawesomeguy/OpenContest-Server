import hashlib
import requests


tokens = dict()  # Create tokens object


def hash(password, salt):
    """Hash password with salt"""

    return salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


def authorize_request(username, homeserver, token):
    """Request an authorization"""

    return requests.post('https://' + homeserver, json={
        'type': 'authorize',
        'username': username,
        'token': token
    }).status_code
