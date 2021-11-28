#!/usr/bin/env python3

import logging
import os
import subprocess
import json

from args import args
from languages import languages

# Construct about object
about = { 'version': '2.1.0', 'languages': dict() }
for name, description in languages.items():
    about['languages'][name] = subprocess.check_output(description.version, shell=True).decode('utf-8')[:-1]
about = json.dumps(about)
logging.debug(about)

# Handle about request
# Return information about this OpenContest server
def about():
    return (200, about)
