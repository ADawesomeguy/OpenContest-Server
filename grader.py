#!/usr/bin/python3

import os
import logging
import argparse
import sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


parser = argparse.ArgumentParser(description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6001, help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail', help='which sandboxing program to use', type=str)
args = parser.parse_args()


#logging.basicConfig(filename='log', level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)


class language:
    def __init__(self, extension, cmd, compile_cmd=''):
        self.extension = extension
        self.cmd = cmd
        self.compile_cmd = compile_cmd


languages = {
    'text/x-c++src': language('cpp', './main', 'g++ main.cpp -o main -O2'),
    'text/x-python': language('py', 'python main.py'),
    'text/x-java': language('java', 'java main', 'javac main.java'),
    'text/x-csrc': language('c', './main', 'gcc main.c -o main -O2'),
    'text/x-csharp': language('cs', 'csc main.cs -out:main.exe', 'mono main.exe'),
    'application/javascript': language('js', 'nodejs main.js'),
    'application/x-ruby': language('rb', 'ruby main.ruby'),
    'application/x-perl': language('pl', 'perl main.pl'),
    'application/x-php': language('php', 'php main.php'),
    'text/x-go': language('go', './main', 'go build main.go'),
    'text/x-rust': language('rs', './main', 'rustc main.rs'),
    'text/x-kotlin': language('kt', 'kotlin main', 'kotlinc main.kt'),
    'text/x-lua': language('lua', 'lua main.lua'),
    'text/x-common-lisp': language('lisp', 'ecl --load main.lisp'),
    'text/x-shellscript': language('sh', './main.sh', 'chmod +x main.sh')
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
                if os.path.isfile('contests/'+contest+'/'+problem): continue
                command += '0, '
            command = command[:-2]+')'
            cur.execute(command)
        cur.execute('UPDATE '+data['contest']+'_status SET P'+data['problem']+' = ? WHERE username = ?', (str(ver), data['username'],))
        con.commit()

        self.send_code(ver)
    

    # Authenticate user
    def authenticate(self, data):
        users = cur.execute('SELECT * FROM users WHERE username = ?', (data['username'],)).fetchall()
        return len(users) == 1 and users[0][3] == data['password']


    # Return info about server
    def about(self, data):
        about = open('about', 'r').read()
        self.send_body(about)


    # Return contests on this server
    def contests(self, data):
        contests = ''
        for contest in os.listdir('contests'):
            contests += contest+'\n'
        self.send_body(contests)
    

    # Register a new user
    def register(self, data):
        if cur.execute('SELECT Count(*) FROM users WHERE username="'+data['username']+'"').fetchone() == 0:
            self.send_code(409)
            return
        cur.execute('INSERT INTO users VALUES ("'+data['names']+'","'+data['emails']+'","'+data['username']+'","'+data['password']+'")')
        con.commit()
        self.send_code(201)
    

    # Return information about a contest
    def info(self, data):
        if not os.path.isdir('contests/'+data['contest']):
            self.send_code(404)
            return
        info = open('contests/'+data['contest']+'/README.md', 'r').read()
        self.send_body(info)
    

    # Return the problems statements for a contest
    def problems(self, data):
        if not os.path.isdir('contests/'+data['contest']):
            self.send_code(404)
            return
        info = open('contests/'+data['contest']+'/problems.pdf', 'rb').read()
        self.send_body(info)


    # Process a submission
    def submit(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests') or data['problem'] not in os.listdir('contests/'+data['contest']):
            self.send_code(404)

        # Save the program
        with open('./main.'+languages[data['lang']].extension, 'w') as f:
            f.write(data['code'])
        os.system('mkdir ~/tmp; mv main* ~/tmp')
        # Sandboxing program
        if args.sandbox == 'firejail': sandbox = 'firejail --profile=firejail.profile bash -c '
        else: sandbox = 'bash -c ' # Dummy sandbox

        # Compile the code if needed
        if languages[data['lang']].compile_cmd != '':
            ret = os.system('cd ~/tmp && '+languages[data['lang']].compile_cmd)
            if ret:
                self.verdict(data, 500)
                return

        tc,tcdir = 1,'contests/'+contest+'/'+problem+'/'
        while os.path.isfile(tcdir+str(tc)+'.in'):
            # Run test case
            os.system('ln '+tcdir+str(tc)+'.in ~/tmp/in')
            ret = os.system(sandbox+'"cd ~/tmp; timeout 1 '+languages[data['lang']].cmd+' < in > out"')
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
        self.send_body(str(status))
    

    # Return user submission history
    def history(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests'):
            self.send_code(404)
            return
        history = cur.execute('SELECT "number","problem","verdict" FROM '+data['contest']+'_submissions WHERE username = ?', (data['username'],)).fetchall()
        self.send_body(str(history))

    
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
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        idx,data = -1,{}
        # Debug this! Not very robust!
        while post_data.find('Content-Disposition', idx+1) != -1:
            idx = post_data.find('Content-Disposition', idx+1)
            key_start = post_data.find('"', idx)+1
            key_end = post_data.find('"', key_start)
            if not post_data[key_start:key_end] == 'file':
                value_start = post_data.find('\r\n', key_end)+4
                value_end = post_data.find('\r\n--', value_start)
                data[post_data[key_start:key_end]] = post_data[value_start:value_end]
            else:
                lang_start = post_data.find(': ', key_end)+2
                lang_end = post_data.find('\r\n', lang_start)
                data['lang'] = post_data[lang_start:lang_end]
                code_start = lang_end+4
                code_end = post_data.find('\r\n--', code_start)
                data['code'] = post_data[code_start:code_end]
        logging.info(data)

        # Remove the try block for debugging
        try:
            request = 'self.'+data['type']+'(data)'
            eval(request)
        except:
            self.send_code(500)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
