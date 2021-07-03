#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
from argparse import ArgumentParser
from pymongo import MongoClient
from operator import itemgetter
from hashlib import sha256, pbkdf2_hmac
from binascii import hexlify
from json import loads, dumps
from jwt import encode, decode

tokenKey = 'tokenKey123'  # TODO: hide token key
db = MongoClient(port=27017).laduecs

# set user schema
db.users.validator = {
    '$jsonSchema': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['_id', 'username', 'password', 'names', 'emails', 'status'],
        'properties': {
            '_id': {'bsonType': 'objectId'},
            'username': {'bsonType': 'string', 'minLength': 3, 'maxLength': 16},
            'password': {'bsonType': 'string'},
            'names': {
                'bsonType': 'array',
                'items': {'bsonType': 'string', 'minLength': 1, 'maxLength': 60}
            },
            'emails': {
                'bsonType': 'array',
                'items': {'bsonType': 'string', 'minLength': 5, 'maxLength': 255}
            },
            'status': {
                'bsonType': 'object',
                'additionalProperties': {
                    'bsonType': 'object',
                    'additionalProperties': {'bsonType': 'int', }
                }
            }
        }
    }
}


class language:
    def __init__(self, extension, cmd, compile_cmd=''):
        self.extension = extension
        self.cmd = cmd
        self.compile_cmd = compile_cmd


languages = {
    'text/x-c++src': language('cpp', './main', 'g++ main.cpp -o main -O2'),
    'text/x-python-script': language('py', 'python main.py'),
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


def hash_password(password):
    salt = sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hexlify(pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000))
    return (salt + pwdhash).decode('ascii')


def process_registration(self, data):  # Process user/team registrations
    try:
        username, password = itemgetter('username', 'password')(data)
        if db.users.find_one({'username': username}):  # ensure unique username
            self.send_response(409)
        else:  # initialize new user
            user = {'username': username, 'password': hash_password(password), 'name': [
            ], 'emails': [], 'status': {}}
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


def verify_password(password, stored_password):
    salt, stored_password = stored_password[:64], stored_password[64:]
    pwdhash = hexlify(pbkdf2_hmac('sha512', password.encode(
        'utf-8'), salt.encode('ascii'), 100000)).decode('ascii')
    return pwdhash == stored_password


def authenticate_user(username, password):  # Verify username and password
    user = db.users.find_one({'username': username})
    return user and verify_password(password, user['password'])


def generate_token(username):
    return encode({'username': username}, tokenKey)


def authenticate_token(username, token):  # TODO: authenticate user token
    return decode(token, tokenKey, 'HS256') == {'username': username}


def process_login(self, data):  # TODO: Login and return token
    token = False
    try:
        username, password = itemgetter('username', 'password')(data)
        if authenticate_user(username, password):
            token = generate_token(username)
            self.send_response(202)
            self.send_header('Content-type', 'text/html')
        else:
            self.send_response(401)
    except Exception:
        self.send_error(400)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.end_headers()
    if token:
        self.wfile.write(dumps(token).encode('utf-8'))


def compile_program(lang, program):
    # Save the program
    with open('main.'+languages[lang].extension, 'w') as f:
        f.write(program)
    os.system('mkdir ~/tmp; mv main* ~/tmp')

    # Sandbox program
    if args.sandbox == 'firejail':
        sandbox = 'firejail --profile=firejail.profile bash -c '
    else:
        sandbox = 'bash -c '

    # Compile the code if needed
    if languages[lang].compile_cmd != '':
        ret = os.system('cd ~/tmp && '+languages[lang].compile_cmd)
        if ret:
            return
    return sandbox


def run_test_cases(sandbox, contest, problem, lang):
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
            return 408

        # Diff the output with the answer
        ret = os.system('diff -w ~/tmp/out ' +
                        tcdir+str(tc)+'.out')
        os.system('rm ~/tmp/out')

        if ret != 0:
            # Wrong answer
            return 406

        tc += 1

    # All correct!
    return 202


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
        print(data)  # TODO: remove
        username, token, contest, problem, lang, program = itemgetter(
            'username', 'token', 'contest', 'problem', 'lang', 'program')(data)
        if authenticate_token(username, token):
            sandbox = compile_program(lang, program)
            if sandbox:
                verdict = run_test_cases(sandbox, contest, problem, lang)
                give_verdict(self, verdict, username, contest, problem)
            else:
                give_verdict(self, 500, username, contest, problem)
        else:
            self.send_response(401)
    except Exception:
        self.send_error(400)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.end_headers()


class FileUploadRequestHandler(BaseHTTPRequestHandler):

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


parser = ArgumentParser(
    description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=7789,
                    help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail',
                    help='which sandboxing program to use', type=str)
args = parser.parse_args()

run()
