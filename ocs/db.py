import logging
import os
import json
from sqlite3 import connect

from ocs.args import args


# Prepare database
database = os.path.join(args.data_dir, 'ocs.db')
logging.debug(database)
con = connect(database, check_same_thread=False)
cur = con.cursor()
logging.info('Database connected')

# Create user table
cur.execute(
    'CREATE TABLE IF NOT EXISTS users (username text unique, name text, email text unique, password text)')


for contest in os.listdir(args.contests_dir):
    """Create contest status table"""

    if contest.startswith('.'):
        continue  # Skip "hidden" contests

    command = 'CREATE TABLE IF NOT EXISTS "' + \
        contest + '_status" (username text, '

    problems = json.load(
        open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
    for problem in problems:
        command += '"' + problem + '" text, '
    command = command[:-2] + ')'

    cur.execute(command)

    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS "' + contest +
                '_submissions" (number real, username text, problem text, code text, verdict real)')
    con.commit()
