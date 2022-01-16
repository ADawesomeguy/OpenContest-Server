import logging
import os
import json
from subprocess import check_output

from ocs.args import args
from ocs.languages import languages


# Construct about object
about_server = {'version': check_output('git describe --long --tags | \
                sed \'s/^v//;s/\\([^-]*-g\\)/r\\1/;s/-/./g\'', shell=True).decode('utf-8'),
                'languages': {}, 'contests': []}

# Get language versions
for name, description in languages.items():
    about_server['languages'][name] = check_output(
        description.version, shell=True).decode('utf-8')[:-1]

# Get contests
for contest in os.listdir(args.contests_dir):
    if contest.startswith('.'):
        continue  # Skip "hidden" contests
    about_server['contests'].append(contest)

# Convert to JSON
about_server = json.dumps(about_server)
logging.debug(about_server)
