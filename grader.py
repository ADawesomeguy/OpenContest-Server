#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import argparse
import sqlite3
from operator import itemgetter
from json import loads, dumps
import jwt


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


con = sqlite3.connect('db')
cur = con.cursor()
cur.execute('''CREATE TABLE users
            (names text, emails text, username text, password text)''')
for 
con.commit()


def process_registration(self, data):  # Process user/team registrations
    try:
        username, password = itemgetter('username', 'password')(data)
        if db.users.find_one({'username': username}):  # ensure unique username
            self.send_response(409)
        else:  # initialize new user
            user = {'username': username, 'password': password, 'name': [
            ], 'emails': [], 'status': {}}  # TODO: hash password, add salt
            db.users.insert_one(user)
            self.send_response(201)
    except Exception:
        self.send_error(400)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.end_headers()


def process_status(self, data):  # Process status queries
    status = {}
    try:
        username, contest = itemgetter('username', 'contest')(data)
        user = db.users.find_one({'username': username})
        if user:
            if contest in user['status']:
                status = user['status'][user['contest']]
            self.send_response(200)
        else:
            self.send_error(404)
    except Exception:
        self.send_error(400)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(dumps(status).encode('utf-8'))


def authenticate_user(username, password):  # Verify username and password
    user = db.users.find_one({'username': username})
    return user and password == user['password']


def authenticate_token(username, token):  # TODO: authenticate user token
    return True


def process_login(self, data):
    username, password = itemgetter('username', 'password')(data)
    process_login(self, username, password)


def process_login(self, username, password):  # TODO: Login and return token
    status = ''
    if authenticate_user(username, password):
        self.send_response(202)
        status = 'TODO: generate login token'
    else:
        self.send_response(501)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(dumps(status).encode('utf-8'))


# def compile_program(lang, program):
#     # Save the program
#     with open('main.'+languages[lang].extension, 'w') as f:
#         f.write(program)
#     os.system('mkdir ~/tmp; mv main* ~/tmp')

#     # Sandbox program
#     if args.sandbox == 'firejail':
#         sandbox = 'firejail --profile=firejail.profile bash -c '
#     else:
#         sandbox = 'bash -c '

#     # Compile the code if needed
#     if languages[lang].compile_cmd != '':
#         ret = os.system('cd ~/tmp && '+languages[lang].compile_cmd)
#         if ret:
#             self.give_verdict(500, username, contest, problem)
#             return

#     tc = 1
#     tcdir = contest+'/'+problem+'/'
#     while os.path.isfile(tcdir+str(tc)+'.in'):
#         # Run test case
#         os.system('ln '+tcdir+str(tc)+'.in ~/tmp/in')
#         ret = os.system(sandbox+'"cd ~/tmp; timeout 1 ' +
#                         languages[lang].cmd+' < in > out"')
#         os.system('rm ~/tmp/in')

#         if ret != 0:
#                 # Runtime error
#                 self.give_verdict(408, username, contest, problem)
#                 return

#             # Diff the output with the answer
#             ret = os.system('diff -w ~/tmp/out '+tcdir+str(tc)+'.out')
#             os.system('rm ~/tmp/out')

#             if ret != 0:
#                 # Wrong answer
#                 self.give_verdict(406, username, contest, problem)
#                 return

#             tc += 1


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    # Save verdict and send back result to the client
    def give_verdict(self, res, username, contest, problem):
        db.users.find_one_and_update({'username': username}, {
                                     '$set': {'status.%s.%s' % (contest, problem): res}})
        print(db.users.find_one({'username': username}))
        os.system('rm -rf ~/tmp')

        self.send_response(res)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # Process a submission
    def process_submission(self, data):
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

    def parse_data(self):
        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        return loads(self.rfile.read(content_length).decode(
            'ascii'))  # Get the data itself

    def do_OPTIONS(self):
        print(self.path)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'X-Requested-With, Content-Type')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # Handle LGP POST requests
    def do_POST(self):
        path, data = self.path, self.parse_data()

        if path == '/user/register':
            process_registration(self, data)
        elif path == '/submit':
            self.process_submission(data)
        else:  # invalid POST
            self.send_response(400)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

    # Handle LGP GET requests
    def do_GET(self):
        path, data = self.path, self.parse_data()

        if path == '/user/login':
            process_login(self, data)
        elif path == '/status':
            process_status(self, data)
        else:  # invalid GET
            self.send_response(400)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)  # 127.0.0.1
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


parser = argparse.ArgumentParser(
    description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=7789,
                    help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail',
                    help='which sandboxing program to use', type=str)
args = parser.parse_args()


run()