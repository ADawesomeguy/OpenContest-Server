#!/usr/bin/env python3

import logging
import os
from sqlite3 import connect

from args import args


# Prepare database
database = os.path.join(args.data_dir, 'data.db')
logging.debug(database)
con = connect(database, check_same_thread=False)
cur = con.cursor()
logging.info('Database connected')
