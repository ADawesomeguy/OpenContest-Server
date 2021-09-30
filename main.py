#!/usr/bin/python3

import os
import logging
import sqlite3
import hashlib
import json
import jwt
import datetime
from base64 import b64decode
from argparse import ArgumentParser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

tokenKey = 'tokenKey123'  # TODO: hide token key

parser = ArgumentParser(
    description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6001,
                    help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail',
                    help='which sandboxing program to use', type=str)
parser.add_argument('-d', '--debug', action='store_true',
                    help='run server in debug mode')
args = parser.parse_args()


#logging.basicConfig(filename='log', level=logging.INFO)
if args.debug:
    logging.basicConfig(level=logging.DEBUG)


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


# Prepare db
con = sqlite3.connect('db', check_same_thread=False)
cur = con.cursor()
# Create user table
cur.execute(
    'CREATE TABLE IF NOT EXISTS users (names text, emails text, username text, password text)')
for contest in os.listdir('contests'):
    # Create contest status table
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status (username text, '
    for problem in os.listdir('contests/'+contest):
        if os.path.isfile('contests/'+contest+'/'+problem) or problem.startswith('.'):
            continue
        command += 'P'+problem+' text, '
    command = command[:-2]+')'
    cur.execute(command)
    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS '+contest +
                '_submissions (number real, username text, problem text, code text, verdict real)')
con.commit()


def hash(password, salt):
    return salt+hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


def verdict(data, ver):  # Save verdict and send back result to the client
    os.system('rm -rf ~/tmp')  # Clean up ~/tmp

    logging.info(ver)

    num = int(cur.execute('SELECT Count(*) FROM ' +
                          data['contest']+'_submissions').fetchone()[0])
    cur.execute('INSERT INTO '+data['contest']+'_submissions VALUES (?, ?, ?, ?, ?)',
                (num, data['username'], data['problem'], data['code'], ver))

    if cur.execute('SELECT Count(*) FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchone()[0] == 0:
        command = 'INSERT INTO '+data['contest'] + \
            '_status VALUES ("'+data['username']+'", '
        for problem in os.listdir('contests/'+data['contest']):
            if os.path.isfile('contests/'+contest+'/'+problem) or problem.startswith('.'):
                continue
            command += '0, '
        command = command[:-2]+')'
        cur.execute(command)
    cur.execute('UPDATE '+data['contest']+'_status SET P'+data['problem'] +
                ' = ? WHERE username = ?', (str(ver), data['username'],))
    con.commit()
    return ver


def authenticate(data):  # Authenticate user: verify password
    users = cur.execute(
        'SELECT * FROM users WHERE username = ?', (data['username'],)).fetchall()
    return len(users) == 1 and users[0][3] == hash(data['password'], users[0][3][:32])


def about():  # Return info about server
    return open('about.json', 'r').read()


def contests():  # Return contests on this server
    contests = ''
    for contest in os.listdir('contests'):
        if contest.startswith('.'):
            continue  # skip "hidden" contests
        contests += contest+'\n'
    return contests


def register(data):  # Register a new user
    if cur.execute('SELECT Count(*) FROM users WHERE username=?', (data['username'],)).fetchone()[0] != 0:
        return 409
    cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                (data['names'], data['emails'], data['username'], hash(data['password'], os.urandom(32))))
    con.commit()
    return 201

def generate_token(username):
    return jwt.encode({'username': username}, tokenKey)

def login(data):  # TODO: Login and return token
    token = False
    try:
        if authenticate(data):
            token = generate_token(data['username'])
            return token
        else:
            return 401
    except Exception:
        return 400

# Return information about a contest


def info(self, data):
    if not os.path.isdir('contests/'+data['contest']):
        self.send_code(404)
        return
    info = open('contests/'+data['contest']+'/info.json', 'r').read()
    self.send_body(info)

def problems(data): # Return the problems statements for a contest
    if not os.path.isdir('contests/'+data['contest']):
        return 404
    info = open('contests/'+data['contest']+'/problems.pdf', 'rb').read()
    return info

def solves(data): # Return number of solves for each problem
    if not os.path.isdir('contests/'+data['contest']):
        return 404
    solves = {}
    for problem in os.listdir('contests/'+data['contest']):
        if os.path.isfile('contests/'+contest+'/'+problem) or problem.startswith('.'):
            continue
        solves[problem] = cur.execute(
            'SELECT COUNT(*) FROM '+data['contest']+'_status WHERE P'+problem+' = 202').fetchone()[0]
    return solves

def submit(data): # Process a submission
    if not authenticate(data) \
            or data['contest'] not in os.listdir('contests') or not os.path.exists('contests/'+data['contest']+'/'+data['problem']) \
            or datetime.datetime.now() < datetime.datetime.fromisoformat(json.loads(open('contests/'+data['contest']+'/info.json', 'r').read())['start-time']):
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

    tcdir = 'contests/'+data['contest']+'/'+problem+'/'
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
    if not authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    status = cur.execute(
        'SELECT * FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchall()
    return status


def history(self, data):  # Return user submission history
    if not authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    history = cur.execute('SELECT "number","problem","verdict" FROM ' +
                          data['contest']+'_submissions WHERE username = ?', (data['username'],)).fetchall()
    return history  # Return this as JSON?

# Return the code for a particular submission


def code(data):
    if not authenticate(data) or data['contest'] not in os.listdir('contests'):
        return 404
    code = cur.execute(
        'SELECT "code" FROM '+data['contest']+'_submissions WHERE username = ? AND number = ?', (data['username'], data['number'])).fetchone()[0]
    return(code)


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    def send(self, body, code=200):  # Send back a status code with no body
        logging.info(body)
        if type(body) == int:
            self.send_response(body)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:  # Send response body
            body = json.dumps(body).encode('utf-8')
            self.send_response(code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Contest-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body)

    def parse_headers(self):
        try:
            auth, auth_content = self.headers['Authorization'].split(' ', 1)
            if auth == 'Basic':
                username, password = b64decode(
                    auth_content).decode('utf-8').split(':', 1)
                return {'username': username, 'password': password}
            elif auth == 'Bearer':
                return {'token': auth_content}
        except Exception:
            return {}

    def parse_data(self):
        try:
            # Get the size of data
            content_length = int(self.headers['Content-Length'])
            return json.loads(self.rfile.read(content_length).decode(
                'ascii'))  # Get the data itself
        except Exception:
            return {}

    def do_OPTIONS(self):  # Handle POST requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'Authorization, Content-Type')
        self.end_headers()

    def do_POST(self):  # Handle POST requests
        path, data, auth = self.path, self.parse_data(), self.parse_headers()
        logging.info(data)
        data.update(auth)
        print(data)

        response = 400
        if path == '/user/register':
            response = register(data)
        elif path == '/submit':
            response = submit(data)

        self.send(response)

    def do_GET(self):  # Handle GET requests
        path, data, auth = self.path, self.parse_data(), self.parse_headers()
        logging.info(data)
        data.update(auth)
        print(data)

        response = 400
        if path == '/about':
            response = about()
        elif path == '/user/login':
            response = login(data)
        elif path == '/status':
            response = status(data)

        self.send(response)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
