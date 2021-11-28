#!/usr/bin/env python3

import os
import hashlib
import sqlite3
from operator import itemgetter
import requests

from db import con, cur

# Create user table
cur.execute(
    'CREATE TABLE IF NOT EXISTS users (username text unique, name text, email text unique, password text)')

# Create tokens object
tokens = dict()

# Hash password with salt
def hash(password, salt):
    return salt + hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

# Handle register request
# Register a new user
def register(name, email, username, password):    
    if cur.execute('SELECT Count(*) FROM users WHERE username=?', (username,)).fetchone()[0] != 0:
        return (409, None)
    
    cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
        (name, email, username, hash(password, os.urandom(32))))
    con.commit()
    return (201, None)

# Handle authenticate request
# Verify username and password
def authenticate(username, password):
    users = cur.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchall()
    if len(users) == 0:
        return (404, None) # Username not found
    
    if users[0][3] == hash(password, users[0][3][:32]):
        # Create and save token
        token = os.urandom(32).encode('base-64')
        if username not in tokens:
            tokens[username] = set()
        tokens[username].add(token)
        return (200, token)
    
    return (403, None) # Incorrect password

# Handle authorize request
# Verify token
def authorize(username, token):
    if cur.execute('SELECT Count(*) FROM users WHERE username=?', (username,)).fetchone()[0] == 0:
        return (404, None) # Username not found
    
    if username not in tokens:
        tokens[username] = set()
    if token in tokens[username]:
        tokens[username].remove(token)
        return (200, None)
    
    return (403, None) # Incorrect token

# Request an authorization
def authorize_request(username, homeserver, token):
    return requests.post(server, json={
        'type': 'authorize',
        'username': username,
        'token': token
    }).status_code
