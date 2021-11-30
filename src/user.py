#!/usr/bin/env python3

import hashlib
import requests

# Create tokens object
tokens = dict()

# Hash password with salt
def hash(password, salt):
    return salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

# Request an authorization
def authorize_request(username, homeserver, token):
    return requests.post('https://' + homeserver, json={
        'type': 'authorize',
        'username': username,
        'token': token
    }).status_code
