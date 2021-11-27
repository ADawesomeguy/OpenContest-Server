#!/usr/bin/env python3

import json
import os
import subprocess

from args import args
from languages import languages


about = { 'version': '2.0.0', 'languages': {} }

for name, description in languages.items():
    about['languages'][name] = subprocess.check_output(description.version, shell=True).decode('utf-8')[:-1]

with open(os.path.join(args.data_dir, 'about.json'), 'w') as f:
    f.write(json.dumps(about))
