#!/usr/bin/env python3

import os
import json

from args import args
from db import con, cur
from about import about_server
import problem

# Handle about request
# Return information about this OpenContest server
def about():
    return (200, about_server)

# Handle contests request
# Return contests on this server
def contests():
    contests = []
    for contest in os.listdir(args.contests_dir):
        if contest.startswith('.'): continue # Skip "hidden" contests
        contests.append(contest)
    return (200, json.dumps(contests))


# Handle info request
# Return information about a contest
def info(contest):
    return (200, open(os.path.join(args.contests_dir, contest, 'info.json'), 'r').read())

# Handle problem request
# Returns a problems statement
def problem(contest, problem):
    return (200, problem.statement(contest, problem))

# Handle solves request
# Return number of solves for each problem
def solves(contest):    
    solves = dict()
    problems = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
    for problem in problems:
        solves[problem] = cur.execute(
            'SELECT COUNT(*) FROM '+contest+'_status WHERE P'+problem+' = 202').fetchone()[0]
    return json.dumps(solves)

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

# Handle submit request
# Process a code submission
def submit(username, homeserver, token, contest, problem, language, code):
    return problem.process(contest, problem, language, code)

# Handle status request
# Return user status
def status(username, homeserver, token, contest):
    status = cur.execute('SELECT * FROM ' + contest + '_status WHERE username = ?', (username,)).fetchall()
    return (200, status)

# Handle history request
# Return user submission history
def history(username, homeserver, token, contest, all):
    history = cur.execute('SELECT "number","problem","verdict" FROM ' + contest +
                          '_submissions WHERE username = ?', (username,)).fetchall()
    return (200, history)

# Handle code request
# Return the code for a particular submission
def code(username, homeserver, token, contest, number):
    code = cur.execute('SELECT "code" FROM ' + contest + '_submissions WHERE username = ? AND number = ?',
                       (username, number)).fetchone()[0]
    return (200, code)

