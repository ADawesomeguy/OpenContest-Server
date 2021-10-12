#!/usr/bin/python3

import os
import logging
import datetime
from args import args

import user
import db

cwd = 'contests/'


class language:
    def __init__(self, extension, cmd, compile_cmd=''):
        self.extension = extension
        self.cmd = cmd
        self.compile_cmd = compile_cmd


languages = {
    'cpp': language('cpp', './main', 'g++ main.cpp -o main -O2'),
    'py': language('py', 'python main.py'),
    'java': language('java', 'java main', 'javac main.java'),
    'c': language('c', './main', 'gcc main.c -o main -O2'),
    'cs': language('cs', 'csc main.cs -out:main.exe', 'mono main.exe'),
    'js': language('js', 'nodejs main.js'),
    'rb': language('rb', 'ruby main.ruby'),
    'pl': language('pl', 'perl main.pl'),
    'php': language('php', 'php main.php'),
    'go': language('go', './main', 'go build main.go'),
    'rs': language('rs', './main', 'rustc main.rs'),
    'kt': language('kt', 'kotlin main', 'kotlinc main.kt'),
    'lua': language('lua', 'lua main.lua'),
    'lisp': language('lisp', 'ecl --load main.lisp'),
    'tcl': language('tcl', 'tclsh main.tcl'),
    'jl': language('jl', 'julia main.jl'),
    'ml': language('ml', 'ocaml main.ml'),
    'hs': language('hs', './main', 'ghc -dynamic main.hs'),
    'sh': language('sh', 'bash main.sh', 'chmod +x main.sh')
}


def contests(_=None):  # Return contests on this server
    # skip hidden contests
    return [dir for dir in next(os.walk(cwd))[1] if not dir.startswith('.')]


def info(data):  # Return information about a contest
    try:
        return open(cwd+data['contest']+'/info.json', 'r').read()
    except KeyError:
        return 400
    except (NotADirectoryError, FileNotFoundError):
        return 404


def problems(data):  # Return the problems statements for a contest
    try:
        return str(open(cwd+data['contest']+'/problems.pdf', 'rb').read())
    except KeyError:
        return 400
    except (NotADirectoryError, FileNotFoundError):
        return 404


def solves(data):  # Return number of solves for each problem
    try:
        contest = data['contest']
        if not os.path.isdir(cwd+contest):
            return 404
        solves = {}
        for problem in next(os.walk(cwd+contest))[1]:
            print(problem)
            if problem.startswith('.'):
                continue
            solves[problem] = db.cur.execute(
                'SELECT COUNT(*) FROM '+contest+'_status WHERE P'+problem+' = 202').fetchone()[0]
        return solves
    except KeyError:
        return 400
    except FileNotFoundError:
        return 404


def verdict(data, ver):  # Save verdict and send back result to the client
    os.system('rm -rf ~/tmp')  # Clean up ~/tmp

    logging.info(ver)

    num = int(db.cur.execute('SELECT Count(*) FROM ' +
                             data['contest']+'_submissions').fetchone()[0])
    db.cur.execute('INSERT INTO '+data['contest']+'_submissions VALUES (?, ?, ?, ?, ?)',
                   (num, data['username'], data['problem'], data['code'], ver))

    if db.cur.execute('SELECT Count(*) FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchone()[0] == 0:
        command = 'INSERT INTO '+data['contest'] + \
            '_status VALUES ("'+data['username']+'", '
        for problem in os.listdir(cwd+data['contest']):
            if os.path.isfile(cwd+contest+'/'+problem) or problem.startswith('.'):
                continue
            command += '0, '
        command = command[:-2]+')'
        db.cur.execute(command)
    db.cur.execute('UPDATE '+data['contest']+'_status SET P'+data['problem'] +
                   ' = ? WHERE username = ?', (str(ver), data['username'],))
    db.cur.commit()
    return ver


def submit(data):  # Process a submission
    if not user.authenticate(data) \
            or data['contest'] not in os.listdir('contests') or not os.path.exists(cwd+data['contest']+'/'+data['problem']) \
            or datetime.datetime.now() < datetime.datetime.fromisoformat(json.loads(open(cwd+data['contest']+'/info.json', 'r').read())['start-time']):
        return 404

    # Save the program
    os.system('mkdir ~/tmp -p')
    with open(os.path.expanduser('~/tmp/main.'+languages[data['language']].extension), 'w') as f:
        f.write(data['code'])
    # Sandboxing program
    if args.sandbox == 'firejail':
        sandbox = 'firejail --profile=firejail.profile bash -c '
    else:
        sandbox = 'bash -c '  # Dummy sandbox

    # Compile the code if needed
    if languages[data['language']].compile_cmd != '':
        ret = os.system('cd ~/tmp && timeout 10 ' +
                        languages[data['language']].compile_cmd)
        if ret:
            verdict(data, 500)
            return

    tcdir = cwd+data['contest']+'/'+problem+'/'
    with open(tcdir+'config.json') as f:
        config = json.loads(f.read())
        time_limit = config['time-limit']
        memory_limit = config['memory-limit']

    tc = 1
    while os.path.isfile(tcdir+str(tc)+'.in'):
        # Run test case
        os.system('ln '+tcdir+str(tc)+'.in ~/tmp/in')
        ret = os.system('ulimit -v '+memory_limit+';'+sandbox+'"cd ~/tmp; timeout '+str(
            time_limit/1000)+languages[data['language']].cmd+' < in > out";ulimit -v unlimited')
        os.system('rm ~/tmp/in')
        if ret != 0:
            verdict(data, 408)  # Runtime error
            return

        # Diff the output with the answer
        ret = os.system('diff -w ~/tmp/out '+tcdir+str(tc)+'.out')
        os.system('rm ~/tmp/out')
        if ret != 0:
            verdict(data, 406)  # Wrong answer
            return
        tc += 1

    verdict(data, 202)  # All correct!


def status(data):  # Return user status
    if not user.authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    status = db.cur.execute(
        'SELECT * FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchall()
    return status


def history(self, data):  # Return user submission history
    if not user.authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    history = db.cur.execute('SELECT "number","problem","verdict" FROM ' +
                             data['contest']+'_submissions WHERE username = ?', (data['username'],)).fetchall()
    return history  # Return this as JSON?

# Return the code for a particular submission


def code(data):
    if not user.authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    code = db.cur.execute(
        'SELECT "code" FROM '+data['contest']+'_submissions WHERE username = ? AND number = ?', (data['username'], data['number'])).fetchone()[0]
    return(code)
