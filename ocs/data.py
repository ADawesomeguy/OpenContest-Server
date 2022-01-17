import logging
import os
from json import load
from subprocess import check_output

from ocs.args import args
from ocs.languages import languages


# TODO: Run this code every time the data changes
# Store data about server, contests, and problems
about_data = {'version': check_output('git describe --long --tags | sed \'s/^v//;s/\\([^-]*-g\\)/r\\1/;s/-/./g\'',
              shell=True).decode('utf-8'), 'languages': {}, 'contests': []}
contest_data = {}
problem_data = {}


# Get language versions
for name, description in languages.items():
    about_data['languages'][name] = check_output(description.version, shell=True).decode('utf-8')[:-1]


# Save information
for contest in os.listdir(args.contests_dir):
    about_data['contests'].append(contest)
    contest_data[contest] = load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))
    problem_data[contest] = {}
    for problem in contest_data[contest]['problems']:
        problem_data[contest][problem] = load(open(os.path.join(
            args.contests_dir, contest, problem, 'info.json'), 'r'))


# Log data
logging.debug(about_data)
logging.debug(contest_data)
logging.debug(problem_data)
