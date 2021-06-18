#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import logging
import pickle


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
        names = self.parse_data(post_data, 'names\"\r\n\r\n', '\r\n--')
        emails = self.parse_data(post_data, 'emails\"\r\n\r\n', '\r\n--')
        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')

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
        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')
        contest = self.parse_data(post_data, 'contest\"\r\n\r\n', '\r\n--')
        problem = self.parse_data(post_data, 'problem\"\r\n\r\n', '\r\n--')
        lang = self.parse_data(post_data, 'Content-Type: ', '\r\n')
        program = self.parse_data(post_data, lang, '\r\n--')

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
            self.give_verdict(500, username, prob)
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
        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')
        contest = self.parse_data(post_data, 'contest\"\r\n\r\n', '\r\n--')

        # Implementation TODO
        self.send_response(406)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


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
        elif request_type == 'query':
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

