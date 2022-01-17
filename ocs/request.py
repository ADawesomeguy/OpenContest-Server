import os
import json

from ocs.data import about_data, contest_data, problem_data
from ocs.db import con, cur
from ocs.user import hash, make_token, check_token
from ocs.problem import statement, process


def about():
    """Return information about this OpenContest server"""

    return (200, json.dumps(about_data))


def info(contest, problem=None):
    """Return information about a contest"""

    if problem is None:
        return (200, json.dumps(contest_data[contest]))
    return (200, json.dumps(problem_data[contest][problem]))


def statement(contest, problem=None):
    """Returns a problems statement"""

    return (200, statement(contest, problem))


def solves(contest, problem=None):
    """Return number of solves for each problem"""

    if problem is None:
        solves = {}
        for problem in contest_data[contest]:
            solves[problem] = cur.execute(
                'SELECT COUNT(*) FROM "' + contest + '_status" WHERE "' + problem + '" = 202').fetchone()[0]
        return (200, json.dumps(solves))
    # TODO: Return JSON
    return (200, cur.execute(
        'SELECT COUNT(*) FROM "' + contest + '_status" WHERE "' + problem + '" = 202').fetchone()[0])


def history(contest, problem=None):
    """Return submissions history"""

    # TODO: Return JSON
    if problem is None:
        return (200, str(cur.execute('SELECT "number","username","homeserver","problem","verdict" FROM "'
                + contest + '_submissions"').fetchall()))
    return (200, str(cur.execute('SELECT "number","username","homeserver","problem","verdict" FROM "'
            + contest + '_submissions" WHERE problem = ?', (problem,)).fetchall()))


def register(name, email, username, password):
    """Register a new user"""

    if cur.execute('SELECT Count(*) FROM users WHERE username = ?', (username,)).fetchone()[0] != 0:
        return 409
    cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (name, email, username, hash(password, os.urandom(32))))
    con.commit()
    return 201


def authenticate(username, password):
    """Verify username and password"""
    
    users = cur.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchall()
    if len(users) == 0:
        return 404  # Username not found
    if users[0][3] == hash(password, users[0][3][:32]):
        return (200, make_token(username))  # Make token
    return 403  # Incorrect password


def authorize(username, token):
    """Verify authentication token"""

    if cur.execute('SELECT Count(*) FROM users WHERE username = ?', (username,)).fetchone()[0] == 0:
        return 404  # Username not found
    if check_token(username, token):
        return (200, None)  # Correct token
    return 403  # Incorrect token


def submit(username, homeserver, token, contest, problem, language, code):
    """Process a code submission"""

    return process(username, contest, problem, language, code)


def status(username, homeserver, token, contest, problem=None):
    """Return user status"""

    # TODO: Return JSON
    if problem is None:
        return (200, str(cur.execute('SELECT * FROM "' + contest +
                '_status" WHERE username = ? AND homeserver = ?', (username, homeserver)).fetchall()))
    return (200, str(cur.execute('SELECT * FROM "' + contest +
            '_status" WHERE username = ? AND homeserver = ? AND problem = ?', (username, homeserver, problem)).fetchall()))


def submissions(username, homeserver, token, contest, problem=None):
    """Return user submission history"""

    # TODO: Return JSON
    if problem is None:
        return (200, str(cur.execute('SELECT "number","problem","verdict" FROM "' + contest +
                '_submissions" WHERE username = ? AND homeserver = ?', (username, homeserver)).fetchall()))
    return (200, str(cur.execute('SELECT "number","verdict" FROM "' + contest +
            '_submissions" WHERE username = ? AND homeserver = ? AND problem = ?', (username, homeserver, problem)).fetchall()))


def code(username, homeserver, token, contest, number):
    """Return the code for a particular submission"""

    if number > int(cur.execute('SELECT Count(*) FROM "' + contest + '_submissions"').fetchone()[0]):
        return 404
    return (200, cur.execute('SELECT "code" FROM "' + contest +
            '_submissions" WHERE username = ? AND homeserver = ? AND number = ?', (username, homeserver, number)).fetchone()[0])
