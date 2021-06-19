#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import logging
import pickle
import argparse


parser = argparse.ArgumentParser(description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6000, help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail', help='which sandboxing program to use', type=str)
args = parser.parse_args()

logging.basicConfig(filename='log', encoding='utf-8', level=logging.INFO)


# Hacky database using pickle
class user:
    def __init__(self, names, emails, username, password):
        self.names = names
        self.emails = emails
        self.username = username
        self.password = password
        self.status = {}


db = {str: user}

if os.path.isfile('db'):
    db = pickle.load(open('db', 'rb'))


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


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    # Find string between left and right in data
    def parse_data(self, data, left, right):
        start = data.find(left)
        end = data.find(right, start)
        ret = data[start+len(left):end]
        logging.info(ret)
        return ret


    # Save verdict and send back result to the client
    def give_verdict(self, res, username, contest, problem):
        logging.info(res)

        # Save to database
        global db
        if contest not in db[username].status:
            db[username].status[contest] = {}
        db[username].status[contest][problem] = res
        
        with open('db', 'wb') as f:
            pickle.dump(db, f)
        
        os.system('rm ~/tmp -rf')
        
        self.send_response(res)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


    # Process user/team registrations
    def process_registration(self, post_data):
        names = self.parse_data(post_data, 'names\"\r\n\r\n', '\r\n--')
        emails = self.parse_data(post_data, 'emails\"\r\n\r\n', '\r\n--')
        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')

        global db
        if username in db:
            self.send_response(418)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:
            db[username] = user(names, emails, username, password)
            
            with open('db', 'wb') as f:
                pickle.dump(db, f)

            self.send_response(201)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
    

    # Process a submission
    def process_submission(self, post_data):
        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')
        contest = self.parse_data(post_data, 'contest\"\r\n\r\n', '\r\n--')
        problem = self.parse_data(post_data, 'problem\"\r\n\r\n', '\r\n--')
        lang = self.parse_data(post_data, 'Content-Type: ', '\r\n')
        program = self.parse_data(post_data, lang, '\r\n--')

        # Check if username and password are valid
        if username not in db or db[username].password != password:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return
        
        # Save the program
        f = open('main.'+languages[lang].extension, 'w')
        f.write(program)
        f.close()
        os.system('mkdir ~/tmp; mv main* ~/tmp')

        # Sandboxing program
        if args.sandbox == 'firejail':
            sandbox = 'firejail --profile=firejail.profile bash -c '
        else:
            sandbox = ''

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
            ret = os.system(sandbox+'"cd ~/tmp; timeout 1 '+languages[lang].cmd+' < in > out"')
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
    

    # Process status queries
    def process_status(self, post_data):
        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')
        contest = self.parse_data(post_data, 'contest\"\r\n\r\n', '\r\n--')

        if username not in db or db[username].password != password:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return

        if contest not in db[username].status:
            status = 'No problems solved'.encode('utf-8')
        else:
            status = str(db[username].status[contest]).encode('utf-8')
        logging.info(status)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(status))
        self.send_header('Contest-Type', 'text/html')
        self.end_headers()
        self.wfile.write(status)


    # Handle LGP POST requests
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        request_type = self.parse_data(post_data, 'type\"\r\n\r\n', '\r\n--')
        if request_type == 'registration':
            self.process_registration(post_data)
        elif request_type == 'submission':
            self.process_submission(post_data)
        elif request_type == 'status':
            self.process_status(post_data)
        else:
            # invalid POST
            self.send_response(501)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()

