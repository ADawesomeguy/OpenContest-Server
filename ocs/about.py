import logging
import os
import json
from subprocess import check_output

from ocs.args import args
from ocs.languages import languages


about = {'version': check_output('git describe --long --tags | sed \'s/^v//;s/\\([^-]*-g\\\
         )/r\\1/;s/-/./g\'', shell=True).decode('utf-8'), 'languages': {}, 'contests': []}
contest_info = {}
problem_info = {}


# Get language versions
for name, description in languages.items():
    about['languages'][name] = check_output(description.version, shell=True).decode('utf-8')[:-1]


# Save information
for contest in os.listdir(args.contests_dir):
    about['contests'].append(contest)
    contest_info[contest] = json.load(open(os.join(args.contest_dir, contest, 'info.json'), 'r'))
    problem_info[contest] = {}
    for problem in contest_info[contest]['problems']:
        problem_info[contest][problem] = json.load(open(os.join(
            args.contest_dir, contest, problem, 'info.json'), 'r'))


# Logging
logging.debug(about)
logging.debug(contest_info)
logging.debug(problem_info)
