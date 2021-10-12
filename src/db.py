#!/usr/bin/python3

import os
import sqlite3

import contest

# Prepare db
con = sqlite3.connect('db', check_same_thread=False)
cur = con.cursor()
print('database connected')

# Create user table
cur.execute(
    'CREATE TABLE IF NOT EXISTS users (names text, emails text, username text, password text)')
for contest in contest.contests():
    # Create contest status table
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status (username text, '
    # skip hidden problems
    for problem in [dir for dir in next(os.walk('contests/'+contest))[1] if not dir.startswith('.')]:
        command += 'P'+problem+' text, '
    command = command[:-2]+')'
    cur.execute(command)
    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS '+contest +
                '_submissions (number real, username text, problem text, code text, verdict real)')
con.commit()
