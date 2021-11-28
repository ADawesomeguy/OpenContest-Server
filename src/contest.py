#!/usr/bin/env python3

import logging
import os
import json

from args import args
from db import con, cur
from user import authorize_request
import problem

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
