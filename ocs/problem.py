import os
from subprocess import run
from requests import post

from ocs.args import args
from ocs.db import con, cur
from ocs.languages import languages


def statement(contest, problem):
    """Get problem statement of local or remote problem"""

    if '@' not in problem:  # Local
        return open(os.path.join(args.contests_dir, contest, problem, 'problem.pdf'), 'rb').read()
    else:  # Remote
        server = problem.split('@')[1]
        return post(server, json={
            'type': problem,
            'contest': contest,
            'problem': problem.split('@')[0]
        }).text


def process(contest, problem, language, code):
    """Process a submission"""

    number = int(cur.execute('SELECT Count(*) FROM ' +
                 contest + '_submissions').fetchone()[0])

    if '@' not in problem:  # Local
        verdict = run_local(contest, problem, language, code, number)
    else:  # Remote
        verdict = run_remote(contest, problem, language, code, number)

    os.rmdir(os.path.join('/tmp', number))  # Clean up ~/tmp

    logging.info(verdict)

    cur.execute('INSERT INTO ' + contest + '_submissions VALUES (?, ?, ?, ?, ?)',
                (number, username, problem, code, verdict))

    if cur.execute('SELECT Count(*) FROM ' + contest + '_status WHERE username = ?', (username,)).fetchone()[0] == 0:
        command = 'INSERT INTO ' + contest + \
            '_status VALUES ("' + username + '", '

        problems = json.load(
            open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))['problems']
        for problem in problems:
            command += '0, '
        command = command[:-2] + ')'
        cur.execute(command)

    cur.execute('UPDATE ' + contest + '_status SET ' + problem +
                ' = ? WHERE username = ?', (str(verdict), username,))
    cur.commit()

    return verdict


def run_local(contest, problem, language, code, number):
    """Run a program locally"""

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
        ret = run('timeout 10 ' + languages[language].compile,
                  shell=True, cwd=os.path.join('/tmp', number))
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
        os.symlink(os.path.join(tcdir, str(tc) + '.in'),
                   os.join('/tmp', number, 'in'))
        # Run test case
        ret = run('ulimit -t ' + str(time_limit / 1000) + '; ' + 'systemd-run --user pm MemoryMax=' + memory_limit +
                  ' -p RestrictNetworkInterfaces=any sh -c "' +
                  languages[language].run +
                  ' < in > out"; ulimit -t unlimited',
                  shell=True, cwd=os.path.join('/tmp', number))
        os.remove(os.path.join('/tmp', number, 'in'))  # Delete input
        if not ret == 0:
            return 408  # Runtime error

        # Diff the output with the answer
        ret = run('diff -w out ' + os.join(tcdir,
                  str(tc) + '.out'), shell=True)
        os.remove(os.path.join('/tmp', number, 'out'))  # Delete output
        if not ret == 0:
            return 406  # Wrong answer
        tc += 1

    return 202  # All correct!


def run_remote(contest, problem, language, code, number):
    """TODO: Run a program remotely"""

    pass
