#!/usr/bin/python3

import os
import logging
import sqlite3
import hashlib
import json
import datetime
from argparse import ArgumentParser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


parser = ArgumentParser(description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6001, help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail', help='which sandboxing program to use', type=str)
parser.add_argument('-d', '--debug', action='store_true', help='run server in debug mode')
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
cur.execute('CREATE TABLE IF NOT EXISTS users (names text, emails text, username text, password text)')
for contest in os.listdir('contests'):
    # Create contest status table
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status (username text, '
    for problem in os.listdir('contests/'+contest):
        if os.path.isfile('contests/'+contest+'/'+problem) or problem.startswith('.'): continue
        command += 'P'+problem+' text, '
    command = command[:-2]+')'
    cur.execute(command)
    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS '+contest+'_submissions (number real, username text, problem text, code text, verdict real)')
con.commit()


def hash(password, salt):
    return salt+hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    # Send back a status code with no body
    def send_code(self, code):
        logging.info(code)
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


    # Send back a response body
    def send_body(self, body):
        if type(body) == str:
            logging.info(body)
            body = str.encode(body)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Contest-Type', 'text/html')
        self.end_headers()
        self.wfile.write(body)


    # Save verdict and send back result to the client
    def verdict(self, data, ver):
        os.system('rm -rf ~/tmp') # Clean up ~/tmp

        logging.info(ver)

        num = int(cur.execute('SELECT Count(*) FROM '+data['contest']+'_submissions').fetchone()[0])
        cur.execute('INSERT INTO '+data['contest']+'_submissions VALUES (?, ?, ?, ?, ?)', (num, data['username'], data['problem'], data['code'], ver))

        if cur.execute('SELECT Count(*) FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchone()[0] == 0:
            command = 'INSERT INTO '+data['contest']+'_status VALUES ("'+data['username']+'", '
            for problem in os.listdir('contests/'+data['contest']):
                if os.path.isfile('contests/'+contest+'/'+problem) or problem.startswith('.'): continue
                command += '0, '
            command = command[:-2]+')'
            cur.execute(command)
        cur.execute('UPDATE '+data['contest']+'_status SET P'+data['problem']+' = ? WHERE username = ?', (str(ver), data['username'],))
        con.commit()

        self.send_code(ver)
    

    # Authenticate user
    def authenticate(self, data):
        users = cur.execute('SELECT * FROM users WHERE username = ?', (data['username'],)).fetchall()
        return len(users) == 1 and users[0][3] == hash(data['password'], users[0][3][:32])


    # Return info about server
    def about(self, data):
        about = open('about.json', 'r').read()
        self.send_body(about)


    # Return contests on this server
    def contests(self, data):
        contests = ''
        for contest in os.listdir('contests'):
            if contest.startswith('.'): continue # skip "hidden" contests
            contests += contest+'\n'
        self.send_body(contests)
    

    # Register a new user
    def register(self, data):
        if cur.execute('SELECT Count(*) FROM users WHERE username=?', (data['username'],)).fetchone()[0] != 0:
            self.send_code(409)
            return
        cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (data['names'],data['emails'],data['username'],hash(data['password'], os.urandom(32))))
        con.commit()
        self.send_code(201)
    

    # Return information about a contest
    def info(self, data):
        if not os.path.isdir('contests/'+data['contest']):
            self.send_code(404)
            return
        info = open('contests/'+data['contest']+'/info.json', 'r').read()
        self.send_body(info)
    

    # Return the problems statements for a contest
    def problems(self, data):
        if not os.path.isdir('contests/'+data['contest']):
            self.send_code(404)
            return
        info = open('contests/'+data['contest']+'/problems.pdf', 'rb').read()
        self.send_body(info)


    # Return number of solves for each problem
    def solves(self, data):
        if not os.path.isdir('contests/'+data['contest']):
            self.send_code(404)
            return
        solves = {}
        for problem in os.listdir('contests/'+data['contest']):
            if os.path.isfile('contests/'+contest+'/'+problem) or problem.startswith('.'): continue
            solves[problem] = cur.execute('SELECT COUNT(*) FROM '+data['contest']+'_status WHERE P'+problem+' = 202').fetchone()[0]
        self.send_body(json.dumps(solves))


    # Process a submission
    def submit(self, data):
        if not self.authenticate(data) \
            or data['contest'] not in os.listdir('contests') or not os.path.exists('contests/'+data['contest']+'/'+data['problem']) \
            or datetime.datetime.now() < datetime.datetime.fromisoformat(json.loads(open('contests/'+data['contest']+'/info.json', 'r').read())['start-time']):
            self.send_code(404)

        # Save the program
        os.system('mkdir ~/tmp -p')
        with open(os.path.expanduser('~/tmp/main.'+languages[data['language']].extension), 'w') as f:
            f.write(data['code'])
        # Sandboxing program
        if args.sandbox == 'firejail': sandbox = 'firejail --profile=firejail.profile bash -c '
        else: sandbox = 'bash -c ' # Dummy sandbox

        # Compile the code if needed
        if languages[data['language']].compile_cmd != '':
            ret = os.system('cd ~/tmp && timeout 10 '+languages[data['language']].compile_cmd)
            if ret:
                self.verdict(data, 500)
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
            ret = os.system('ulimit -v '+memory_limit+';'+sandbox+'"cd ~/tmp; timeout '+str(time_limit/1000)+languages[data['language']].cmd+' < in > out";ulimit -v unlimited')
            os.system('rm ~/tmp/in')
            if ret != 0:
                self.verdict(data, 408) # Runtime error
                return

            # Diff the output with the answer
            ret = os.system('diff -w ~/tmp/out '+tcdir+str(tc)+'.out')
            os.system('rm ~/tmp/out')
            if ret != 0:
                self.verdict(data, 406) # Wrong answer
                return
            tc += 1

        self.verdict(data, 202) # All correct!
    

    # Return user status
    def status(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests'):
            self.send_code(404)
            return
        status = cur.execute('SELECT * FROM '+data['contest']+'_status WHERE username = ?', (data['username'],)).fetchall()
        self.send_body(str(status)) # Return this as JSON?
    

    # Return user submission history
    def history(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests'):
            self.send_code(404)
            return
        history = cur.execute('SELECT "number","problem","verdict" FROM '+data['contest']+'_submissions WHERE username = ?', (data['username'],)).fetchall()
        self.send_body(str(history)) # Return this as JSON?

    
    # Return the code for a particular submission
    def code(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests'):
            self.send_code(404)
            return
        code = cur.execute('SELECT "code" FROM '+data['contest']+'_submissions WHERE username = ? AND number = ?', (data['username'], data['number'])).fetchone()[0]
        self.send_body(str(code))


    # Handle LGP POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('utf-8') # Get the data itself
        logging.info(post_data)

        data = json.loads(post_data) # Parse JSON
        logging.info(data)
        
        if any(not c.islower() for c in data['type']): # Hopefully protect against arbitrary code execution in the eval below
            self.send_code(501)

        if args.debug:
            eval('self.'+data['type']+'(data)')
            return
        try:
            eval('self.'+data['type']+'(data)') # Dangerous hack
        except:
            self.send_code(500)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()