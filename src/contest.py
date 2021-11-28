#!/usr/bin/env python3

import logging
import os
import json
from datetime import dattime
from operator import itemgetter

from args import args
from db import con, cur
from user import authorize_request
from problem import test

# Create contest status table
for contest in os.listdir(args.contests_dir):
    if contest.startswith('.'):
        continue # Skip "hidden" contests
    
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status (username text, '
    
    problems = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
    for problem in problems:
        command += problem + ' text, '
    command = command[:-2] + ')'

    cur.execute(command)
    
    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS ' + contest +
                '_submissions (number real, username text, problem text, code text, verdict real)')
    con.commit()

# Handle contests request
# Return contests on this server
def contests(data):
    contests = []
    for contest in os.listdir(args.contests_dir):
        if contest.startswith('.'): continue # Skip "hidden" contests
        contests.append(contest)
    return (200, json.dumps(contests))

# Handle info request
# Return information about a contest
def info(data):
    try:
        contest = data['contest']
    except KeyError:
        return (400, None)

    try:
        return (200, open(os.path.join(args.contests_dir, contest, 'info.json'), 'r').read())
    except (NotADirectoryError, FileNotFoundError):
        return (404, None)

# Handle problem request
# Returns a problems statement
def problem(data):
    try:
        contest, problem = itemgetter('contest', 'problem')(data)
    except KeyError:
        return (400, None)
    
    try:
        problems = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
    except NotADirectoryError:
        return (404, None)
    if problem not in problems:
        return (404, None)
    
    return (200, problem.statement(contest, problem))

# Handle solves request
# Return number of solves for each problem
def solves(data):
    try:
        contest = data['contest']
    except KeyError:
        return 400
    
    if not os.path.isdir(os.path.join(args.contests_dir, contest)):
        return 404
    
    solves = dict()
    problems = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
    for problem in problems:
        solves[problem] = cur.execute(
            'SELECT COUNT(*) FROM '+contest+'_status WHERE P'+problem+' = 202').fetchone()[0]
    return json.dumps(solves)

# Handle submit request
# Process a code submission
def submit(data):
    try:
        username, server, token, contest, problem, language, code = itemgetter(
            'username', 'server', 'token', 'contest', 'problem', 'language', code)[data]
    except KeyError:
        return (400, None)
    
    authorization = user.authorize_request(username, server, token)
    if not authorization == 200:
        return (authorization, None)
    
    try:
        problems = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
    except NotADirectoryError:
        return (404, None)
    if problem not in problems or datetime.now() < datetime.fromisoformat(json.loads(
        open(os.path.join(args.contests_dir, contest, 'info.json'), 'r').read())['start-time']):
        return (404, None)

    problem.process(contest, problem, language, code)

# Handle status request
# Return user status
def status(data):
    try:
        username, server, token, contest = itemgetter('username', 'server', 'token', 'contest')(data)
    except KeyError:
        return (400, None)

    authorization = user.authorize_request(username, server, token)
    if not authorization == 200:
        return (authorization, None)
    
    status = cur.execute('SELECT * FROM ' + contest + '_status WHERE username = ?', (username,)).fetchall()
    return (200, status)

# Handle history request
# Return user submission history
def history(data):
    try:
        username, server, token, contest = itemgetter('username', 'server', 'token', 'contest')(data)
    except KeyError:
        return (400, None)

    authorization = user.authorize_request(username, server, token)
    if not authorization == 200:
        return (authorization, None)
    
    history = cur.execute('SELECT "number","problem","verdict" FROM ' + contest +
                          '_submissions WHERE username = ?', (username,)).fetchall()
    return (200, history)

# Handle code request
# Return the code for a particular submission
def code(data):
    try:
        username, server, token, contest, number = itemgetter(
            'username', 'server', 'token', 'contest', 'number')(data)
    except KeyError:
        return (400, None)

    authorization = user.authorize_request(username, server, token)
    if not authorization == 200:
        return (authorization, None)
    
    code = cur.execute('SELECT "code" FROM ' + contest + '_submissions WHERE username = ? AND number = ?',
                       (username, number)).fetchone()[0]
    return (200, code)
