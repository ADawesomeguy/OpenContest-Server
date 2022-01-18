import logging
import os
from sqlite3 import connect

from ocs.data import about_data, contest_data
from ocs.args import args


# Prepare database
con = connect(os.path.join(args.data_dir, 'ocs.db'), check_same_thread=False)
cur = con.cursor()
logging.info('Database connected')


# Create user table
cur.execute('CREATE TABLE IF NOT EXISTS users (name text, email text unique, username text unique, password text)')


for contest in about_data['contests']:
    # Create contest status table
    command = 'CREATE TABLE IF NOT EXISTS "' + contest + '_status" (username text, homeserver text, '
    for problem in contest_data[contest]['problems']:
        command += '"' + problem + '" text, '
    cur.execute(command[:-2] + ')')

    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS "' + contest +
                '_submissions" (number real, username text, homeserver text, problem text, code text, verdict real)')
con.commit()
