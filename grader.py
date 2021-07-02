#!/usr/bin/python3

import os
import logging
import argparse
import sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from email.parser import BytesParser


parser = argparse.ArgumentParser(
    description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6000,
                    help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail',
                    help='which sandboxing program to use', type=str)
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
    command = 'CREATE TABLE IF NOT EXISTS '+contest+'_status ('
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
        pass

    # Return information about a contest
    def info(self, data):
        pass

    # Save verdict and send back result to the client
    def give_verdict(self, res, username, contest, problem):
        db.users.find_one_and_update({'username': username}, {
                                     '$set': {'status.%s.%s' % (contest, problem): res}})
        print(db.users.find_one({'username': username}))
        os.system('rm -rf ~/tmp')

        self.send_code(res)

    # Process a submission
    def submit(self, data):
        try:
            print(data)
            username, token, contest, problem, lang, program = itemgetter(
                'username', 'token', 'contest', 'problem', 'lang', 'program')(data)

            if authenticate_token(username, token):
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
                        self.give_verdict(500, username, contest, problem)
                        return

                tc = 1
                tcdir = contest+'/'+problem+'/'
                while os.path.isfile(tcdir+str(tc)+'.in'):
                    # Run test case
                    os.system('ln '+tcdir+str(tc)+'.in ~/tmp/in')
                    ret = os.system(sandbox+'"cd ~/tmp; timeout 1 ' +
                                    languages[lang].cmd+' < in > out"')
                    os.system('rm ~/tmp/in')

                    if ret != 0:
                        # Runtime error
                        self.give_verdict(408, username, contest, problem)
                        return

                    # Diff the output with the answer
                    ret = os.system('diff -w ~/tmp/out '+tcdir+str(tc)+'.out')
                    os.system('rm ~/tmp/out')

                    if ret != 0:
                        # Wrong answer
                        self.give_verdict(406, username, contest, problem)
                        return

                    tc += 1

                # All correct!
                self.give_verdict(202, username, contest, problem)
            else:
                self.send_response(401)
        except Exception:
            self.send_error(400)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    # Return user status
    def status(self, data):
        pass

    # Return user submission history
    def history(self, data):
        pass
    
    # Return the code for a particular submission
    def code(self, data):
        pass

    # Handle LGP POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        idx = -1
        data = {}
        # Clean up this?
        while post_data.find('Content-Disposition', idx+1) != -1:
            idx = post_data.find('Content-Disposition', idx+1)
            key_start = post_data.find('"', idx)+1
            key_end = post_data.find('"', key_start)
            key = post_data[key_start:key_end]
            if not key == 'file':
                value_start = post_data.find('\r\n', key_end)+4
                value_end = post_data.find('\r\n--', value_start)
                value = post_data[value_start:value_end]
            else:
                lang_start = key_end+17
                lang_end = post_data.find('\r\n', lang_start)
                lang = post_data[lang_start:lang_end]
                code_start = lang_end+4
                code_end = post_data.find('\r\n--', code_start)
                code = post_data[code_start:code_end]
                value = (lang, code)
            data[key] = value
        logging.info(data)

        try:
            request = 'self.'+data['type']+'(data)'
            eval(request)
        except:
            self.send_code(501)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
