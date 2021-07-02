#!-/usr/bin/python3

import os
import logging
import argparse
import sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from email.parser import BytesParser


parser = argparse.ArgumentParser(description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6000, help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail', help='which sandboxing program to use', type=str)
args = parser.parse_args()


logging.basicConfig(filename='log', encoding='utf-8', level=logging.INFO)


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
con = sqlite3.connect('db')
cur = con.cursor()
# Create user table
cur.execute('CREATE TABLE IF NOT EXISTS users (names text, emails text, username text, password text)')
for contest in os.listdir('contests'):
    # Create contest status table
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status (username text, '
    for problem in os.listdir('contests/'+contest):
        command += 'P'+problem+' text, '
    command = command[:-2]+')'
    cur.execute(command)
    # Create contest submissions table
    cur.execute('CREATE TABLE IF NOT EXISTS '+contest+'_submissions (number real, username text, code text, verdict real)')
# Save changes to db
con.commit()


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    # Send back a status code with no body
    def send_code(self, code):
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


    # Send back a response body
    def send_body(self, body):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.send_header('Contest-Type', 'text/html')
        self.end_headers()
        self.wfile.write(body)


    # Save verdict and send back result to the client
    def verdict(self, data, ver):
        num = cur.execute('SELECT Count(*) FROM '+data['contest']+'_submissions').fetchone()
        cur.execute('INSERT INTO '+data['contest']+'_submissions'+' VALUES (? ? ? ?)', (num, data['username'], data['code'], ver))
        con.commit()

        os.system('rm -rf ~/tmp') # Clean up ~/tmp

        self.send_code(res)
    

    # Authenticate user
    def authenticate(self, data):
        users = cur.execute('SELECT * FROM users WHERE username = ?', data['username']).fetchall()
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
        if len(cur.execute('SELECT FROM users WHERE username="'+data['username']+'"').fetchall()):
            self.send_code(409)
            return
        cur.execute('INSERT INTO users VALUES ("'+data['names']+'","'+data['emails']+'","'+data['username']+'","'+data['password']+'")')
        con.commit()
        self.send_code(201)
    

    # Return information about a contest
    def info(self, data):
        if not os.exists('contests/'+data['contest']):
            self.send_code(404)
            return
        info = open('contests/'+data['contest']+'/info', 'r').read()
        self.send_body(info)


    # Process a submission
    def submit(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests') or data['problem'] not in os.listdir('contests/'+data['contest']):
            self.send_code(404)

        # Save the program
        with open('./main.'+languages[lang].extension, 'w') as f:
            f.write(program)
        os.system('mkdir ~/tmp; mv main* ~/tmp')
        # Sandboxing program
        if args.sandbox == 'firejail':
            sandbox = 'firejail --profile=firejail.profile bash -c '
        else:
            sandbox = 'bash -c '

        # Compile the code if needed
        if languages[lang].compile_cmd != '':
            ret = os.system('cd ~/tmp && '+languages[lang].compile_cmd)
            if ret:
                self.verdict(data, 500)
                return

        tc = 1
        tcdir = 'contests/'+contest+'/'+problem+'/'
        while os.path.isfile(tcdir+str(tc)+'.in'):
            # Run test case
            os.system('ln '+tcdir+str(tc)+'.in ~/tmp/in')
            ret = os.system(sandbox+'"cd ~/tmp; timeout 1 '+languages[lang].cmd+' < in > out"')
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
        
        status = cur.execute('SELECT FROM '+data['contest']+'_status WHERE username = ?', data['username']).fetchall()
        self.send_body(status)
    

    # Return user submission history
    def history(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests'):
            self.send_code(404)

        history = cur.execute('SELECT FROM '+data['contest']+'_submissions WHERE username = ?', data['username']).fetchall()
        self.send_body(history)

    
    # Return the code for a particular submission
    def code(self, data):
        if not self.authenticate(data) or data['contest'] not in os.listdir('contests'):
            self.send_code(404)
        
        code = cur.execute('SELECT FROM '+data['contest']+'_submssions WHERE username = ? AND number = ?', (data['username'], data['number'])).fetchall()
        self.send_body(history)
        


    # Handle LGP POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        idx = -1
        data = {}
        while post_data.find('Content-Disposition', idx+1) != -1:
            idx = post_data.find('Content-Disposition', idx+1)
            key_start = post_data.find('"', idx)+1
            key_end = post_data.find('"', key_start)
            if not post_data[key_start:key_end] == 'file':
                value_start = post_data.find('\r\n', key_end)+4
                value_end = post_data.find('\r\n--', value_start)
                data[post_data[key_start:key_end]] = post_data[value_start:value_end]
            else:
                lang_start = key_end+17
                lang_end = post_data.find('\r\n', lang_start)
                data['lang'] = post_data[lang_start:lang_end]
                code_start = lang_end+4
                code_end = post_data.find('\r\n--', code_start)
                data['code'] = post_data[code_start:code_end]
        logging.info(data)

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
