#!/usr/bin/env python3

import os
import requests

from db import con, cur
from languages import languages

# Get problem statement of local or remote problem
def statement(contest, problem):
    if '@' not in problem: # Local
        return open(os.path.join(args.contests_dir, contest, problem, 'problem.pdf'), 'rb').read()
    else: # Remote
        server = problem.split('@')[1]
        return requests.post(server, json={
            'type': problem,
            'contest': contest,
            'problem': problem.split('@')[0]
        }).text

# Process a submission
def process(contest, problem, language, code):
    number = int(cur.execute('SELECT Count(*) FROM ' + contest + '_submissions').fetchone()[0])

    if '@' not in problem: # Local
        verdict = run_local(contest, problem, language, code, number)
    else: # Remote
        verdict = run_remote(contest, problem, language, code, number)
    
    os.rmdir(os.path.join('/tmp', number))  # Clean up ~/tmp

    logging.info(verdict)

    cur.execute('INSERT INTO ' + contest + '_submissions VALUES (?, ?, ?, ?, ?)',
                (number, username, problem, code, verdict))

    if cur.execute('SELECT Count(*) FROM ' + contest +'_status WHERE username = ?', (username,)).fetchone()[0] == 0:
        command = 'INSERT INTO ' + contest + '_status VALUES ("' + username + '", '
        
        problems = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
        for problem in problems:
            command += '0, '
        command = command[:-2] + ')'
        cur.execute(command)
    
    cur.execute('UPDATE '+ contest + '_status SET ' + problem + ' = ? WHERE username = ?', (str(verdict), username,))
    cur.commit()

    return verdict

# Run a program locally
def run_local(contest, problem, language, code, number):
    # Save the program
    os.mkdir(os.path.join('/tmp', number))
    with open(os.path.join('/tmp', number, 'main.' + language, 'w')) as f:
        f.write(code)
    
    # Sandboxing program
    if args.sandbox == 'firejail':
        sandbox = 'firejail --profile=firejail.profile bash -c '
    else:
        sandbox = 'bash -c '  # Dummy sandbox

    # Compile the code if needed
    if not languages[language].compile == None:
        ret = os.system('timeout 10 ' + languages[language].compile, cwd=os.path.join('/tmp', number))
        if ret:
            return 500

    tcdir = os.path.join(args.contest_dir, contest, problem)
    with open(os.path.join(tcdir, 'config.json')) as f:
        config = json.loads(f.read())
        time_limit = config['time-limit']
        memory_limit = config['memory-limit']

    tc = 1
    while os.path.isfile(os.path.join(tcdir, str(tc) + '.in')):
        # Link test data
        os.symlink(os.path.join(tcdir, str(tc) + '.in'), os.join('/tmp', number, 'in'))
        # Run test case
        ret = os.system('ulimit -t ' + str(time_limit / 1000) + '; ' + 'systemd-run --user pm MemoryMax=' + memory_limit + \
            ' -p RestrictNetworkInterfaces=any sh -c "' + languages[language].run + ' < in > out"; ulimit -t unlimited', \
            cwd=os.path.join('/tmp', number))
        os.remove(os.path.join('/tmp', number, 'in')) # Delete input
        if not ret == 0:
            return 408 # Runtime error

        # Diff the output with the answer
        ret = os.system('diff -w out ' + os.join(tcdir, str(tc) + '.out'))
        os.remove(os.path.join('/tmp', number, 'out')) # Delete output
        if not ret == 0:
            return 406 # Wrong answer
        tc += 1

    return 202  # All correct!

# TODO: Run a program remotely
def run_remote(contest, problem, language, code, number):
    pass
