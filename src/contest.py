#!/usr/bin/env python3

import logging
import os
import json
import datetime

from args import args
from db import con, cur
import user
import problem

# Handle contests requests
# Return contests on this server
def contests(data):
    contests = []
    for c in os.listdir(args.contests_dir):
        if c.startswith('.'): continue # Skip "hidden" contests
        contests.append(c)
    return (200, json.dumps(contests))

# Handle info requests
# Return information about a contest
def info(data):
    try:
        return (200, open(os.path.join(args.contests_dir, 'info.json'), 'r').read())
    except KeyError:
        return (400, None)
    except (NotADirectoryError, FileNotFoundError):
        return (404, None)


def problems(data):  # Return the problems statements for a contest
    try:
        return str(open(cwd+data['contest']+'/problems.pdf', 'rb').read())
    except KeyError:
        return 400
    except (NotADirectoryError, FileNotFoundError):
        return 404


def solves(data):  # Return number of solves for each problem
    try:
        contest = data['contest']
        if not os.path.isdir(cwd+'contests/'+contest):
            return 404
        solves = {}
        for problem in next(os.walk(cwd+contest))[1]:
            if problem.startswith('.'):
                continue
            solves[problem] = cur.execute(
                'SELECT COUNT(*) FROM '+contest+'_status WHERE P'+problem+' = 202').fetchone()[0]
        return solves
    except KeyError:
        return 400
    except FileNotFoundError:
        return 404





def status(data):  # Return user status
    if not user.authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    status = cur.execute(
        'SELECT * FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchall()
    return status


def history(data):  # Return user submission history
    if not user.authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    history = cur.execute('SELECT "number","problem","verdict" FROM ' +
                          data['contest']+'_submissions WHERE username = ?', (data['username'],)).fetchall()
    return history  # Return this as JSON?

# Return the code for a particular submission


def code(data):
    if not user.authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    code = cur.execute(
        'SELECT "code" FROM '+data['contest']+'_submissions WHERE username = ? AND number = ?', (data['username'], data['number'])).fetchone()[0]
    return(code)


# Create contest status table
for contest in contests():
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status (username text, '
    # skip hidden problems
    for problem in [dir for dir in next(os.walk(cwd+contest))[1] if not dir.startswith('.')]:
        command += 'P'+problem+' text, '
    command = command[:-2]+')'
    cur.execute(command)
    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS '+contest +
                '_submissions (number real, username text, problem text, code text, verdict real)')
    cur.commit()
