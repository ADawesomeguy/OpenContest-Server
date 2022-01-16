import os
import json
from secrets import token_hex

from ocs.args import args
from ocs.db import con, cur
from ocs.about import about_server
from ocs.user import hash, tokens
from ocs.problem import statement


def about():
    """Return information about this OpenContest server"""

    return (200, about_server)


def info(contest, problem=None):
    """Return information about a contest"""

    if problem is None:
        return (200, open(os.path.join(args.contests_dir,
                contest, 'info.json'), 'r').read())
    return (200, open(os.path.join(args.contests_dir,
            contest, problem, 'info.json'), 'r').read())


def problem(contest, problem=None):
    """Returns a problems statement"""

    return (200, statement(contest, problem))


def solves(contest, problem=None):
    """Return number of solves for each problem"""
    if problem is None:
        solves = dict()
        problems = json.load(
            open(
                os.path.join(
                    args.contests_dir,
                    contest,
                    'info.json'),
                'r'))['problems']
        for problem in problems:
            solves[problem] = cur.execute(
                'SELECT COUNT(*) FROM "' + contest + '_status" WHERE "' + problem + '" = 202').fetchone()[0]
        return (200, json.dumps(solves))
    return (200, cur.execute(
        'SELECT COUNT(*) FROM "' + contest + '_status" WHERE "' + problem + '" = 202').fetchone()[0])


def history(contest, problem=None):
    """Return submissions history"""

    if problem is None:
        return (200, cur.execute(
            'SELECT "number","problem","verdict" FROM "' + contest + '_submissions"').fetchall())
    else:
        return (200, cur.execute(
            'SELECT "number","problem","verdict" FROM "' + contest + '_submissions" WHERE problem = ?', (problem,)).fetchall())


def register(name, email, username, password):
    """Register a new user"""

    if cur.execute('SELECT Count(*) FROM users WHERE username = ?',
                   (username,)).fetchone()[0] != 0:
        return 409
    cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                (name, email, username, hash(password, os.urandom(32))))
    con.commit()
    return 201


def authenticate(username, password):
    """Verify username and password"""
    
    users = cur.execute(
        'SELECT * FROM users WHERE username = ?', (username,)).fetchall()
    if len(users) == 0:
        return 404  # Username not found
    if users[0][3] == hash(password, users[0][3][:32]):
        token = token_hex(32)
        if username not in tokens:
            tokens[username] = set()
        tokens[username].add(token)
        return (200, token)
    return 403  # Incorrect password


def authorize(username, token):
    """Verify authentication token"""

    if cur.execute('SELECT Count(*) FROM users WHERE username = ?',
                   (username,)).fetchone()[0] == 0:
        return 404  # Username not found
    if username not in tokens:
        tokens[username] = set()
    if token in tokens[username]:
        tokens[username].remove(token)
        return (200, None)
    return 403  # Incorrect token


def submit(username, homeserver, token, contest, problem, language, code):
    """Process a code submission"""

    return problem.process(contest, problem, language, code)


def status(username, homeserver, token, contest, problem=None):
    """Return user status"""

    if problem is None:
        return (200, cur.execute('SELECT * FROM ' + contest + '_status WHERE username = ?',
                                 (username,)).fetchall())
    return (200, cur.execute('SELECT * FROM ' + contest +
                             '_status WHERE username = ? AND problem = ?', (username, problem)).fetchall())


def submissions(username, homeserver, token, contest, problem=None):
    """Return user submission history"""

    if problem is None:
        return (200, cur.execute('SELECT "number","problem","verdict" FROM ' + contest +
                                 '_submissions WHERE username = ?', (username,)).fetchall())
    return (200, cur.execute('SELECT "number","problem","verdict" FROM ' + contest +
            '_submissions WHERE username = ? AND problem = ?', (username, problem)).fetchall())


def code(username, homeserver, token, contest, number):
    """Return the code for a particular submission"""

    return (200, cur.execute('SELECT "code" FROM ' + contest +
                             '_submissions WHERE username = ? AND number = ?', (username, number)).fetchone()[0])
