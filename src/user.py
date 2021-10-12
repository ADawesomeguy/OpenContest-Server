#!/usr/bin/python3

import os
import hashlib
from operator import itemgetter
# import jwt

import db


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
    if db.cur.execute('SELECT Count(*) FROM users WHERE username=?', (username,)).fetchone()[0] != 0:
        return 409
    db.cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                   (name, email, username, hash(password, os.urandom(32))))
    db.con.commit()
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
    users = db.cur.execute(
        'SELECT * FROM users WHERE username = ?', (data['username'],)).fetchall()
    return len(users) == 1 and users[0][3] == hash(data['password'], users[0][3][:32])
