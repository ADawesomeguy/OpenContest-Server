#!/usr/bin/env python3

from sqlite3 import connect

# Prepare db
con = connect('db', check_same_thread=False)
cur = con.cursor()
print('database connected')