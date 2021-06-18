#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import logging
import pickle
from json import loads as parse_data

logging.basicConfig(filename='log', encoding='utf-8', level=logging.INFO)


# Hacky database using pickle
class user:
    password = str
    status = {str: {}}
    __init__(self, password):
        self.password = password


db = {str: user}

if os.path.isfile('db'):
    db = pickle.load(open('db', 'rb'))


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    # Save verdict and send back result to the client

    def give_verdict(self, res, username, contest, problem):
        logging.info(res)

        # Save to database
        if contest not in db[username].status:
            db[username].status[contest] = {}
        db[username].status[contest][problem] = res
        pickle.dump(db, open('db', 'wb'))

        os.system('rm main*')

        self.send_response(res)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # Process user/team registrations

    def process_registration(self, post_data):
        post_data = parse_data(post_data)
        names = post_data['names']
        emails = post_data['emails']
        username = post_data['username']
        password = post_data['password']

        if username in db:
            self.send_response(406)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:
            db[username] = user(password)
            self.send_response(202)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

    # Process a submission

    def process_submission(self, post_data):
        post_data = parse_data(post_data)
        username = post_data['username']
        password = post_data['password']
        contest = post_data['contest']
        problem = post_data['problem']
        lang = post_data['lang']
        program = post_data['program']

        # Refactor this especially when adding support for more languages??
        ret = 0
        if lang == 'text/x-c++src':
            f = open('main.cpp', 'w')
            f.write(program)
            f.close()
            ret = os.system('g++ main.cpp -o main -O2')
        elif lang == 'text/x-python':
            f = open('main.py', 'w')
            f.write(program)
            f.close()

        if ret:
            self.give_verdict(500, username, problem)
            return

        tc = 1
        tcdir = contest+'/'+problem+'/'
        while os.path.isfile(tcdir+str(tc)+'.in'):
            if lang == 'text/x-c++src':
                cmd = './main'
            elif lang == 'text/x-python':
                cmd = 'python main.py'

            ret = os.system('timeout 1 '+cmd+' < '+tcdir+str(tc)+'.in > out')

            if ret == 124:
                self.give_verdict(408, username, contest, problem)
                return

            ret = os.system('diff -w out '+tcdir+str(tc)+'.out')
            os.system('rm out')

            if ret != 0:
                self.give_verdict(406, username, contest, problem)
                return

            tc += 1

        self.give_verdict(202, username, contest, problem)

    # Process status queries

    def proccess_status(self, post_data):
        post_data = parse_data(post_data)
        username = post_data['username']
        password = post_data['password']
        contest = post_data['contest']

        # Implementation TODO
        self.send_response(406)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    # Handle LGP POST requests

    def do_POST(self):
        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode(
            'ascii')  # Get the data itself
        logging.info(post_data)

        # self.parse_data(post_data, 'type\"\r\n\r\n', '\r\n--')
        request_type = self.path
        if request_type == '/registration':
            self.process_registration(post_data)
        elif request_type == '/submission':
            self.process_submission(post_data)
        elif request_type == '/query':
            self.process_submission(post_data)
        else:
            # invalid POST
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', 6000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
