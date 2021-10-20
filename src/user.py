#!/usr/bin/env python3

import os
import hashlib
import sqlite3
from operator import itemgetter
# import jwt

from db import con, cur


def hash(password, salt):
    return salt+hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


def generate_token(username):
    return username
    # return jwt.encode({'sub': username}, tokenKey)


def register(data):  # Register a new user
    try:
        username, password, name, email = itemgetter(
            'username', 'password', 'name', 'email')(data)
    except KeyError:
        return 400
    try:
        cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                (name, email, username, hash(password, os.urandom(32))))
        con.commit()
    except sqlite3.IntegrityError:
        return 409
    return generate_token(username), 201


def login(data):  # TODO: Login and return token
    token = False
    try:
        if authenticate(data):
            token = generate_token(data['username'])
            return token
        else:
            return 401
    except Exception:
        return 400


def authenticate(data):  # Authenticate user: verify password
    users = cur.execute(
        'SELECT * FROM users WHERE username = ?', (data['username'],)).fetchall()
    return len(users) == 1 and users[0][3] == hash(data['password'], users[0][3][:32])


# Create user table
cur.execute(
    'CREATE TABLE IF NOT EXISTS users (username text unique, name text, email text unique, password text)')
