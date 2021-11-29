#!/usr/bin/env python3

import logging
import subprocess
import json

from args import args
from languages import languages

# Construct about object
about_server = { 'version': '2.1.0', 'languages': dict() }
for name, description in languages.items():
    about_server['languages'][name] = subprocess.check_output(description.version, shell=True).decode('utf-8')[:-1]
about_server = json.dumps(about_server)
logging.debug(about_server)
