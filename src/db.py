#!/usr/bin/env python3

from sqlite3 import connect

from var import cwd

# Prepare db
con = connect(cwd+'db', check_same_thread=False)
cur = con.cursor()
print('database connected')