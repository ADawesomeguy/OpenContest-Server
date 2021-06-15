#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import logging
import pickle

logging.basicConfig(filename='log', encoding='utf-8', level=logging.INFO)

class user:
    password = 'password'
    status = {}

data = {'test': user()}

if os.path.isfile('data'):
    data = pickle.load(open('data', 'rb'))


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    # Find string between left and right in data
    # Don't shadow the global data var??
    def parse_data(self, data, left, right):
        start = data.find(left)
        end = data.find(right, start)
        ret = data[start+len(left):end]
        logging.info(ret)
        return ret


    # Save verdict and send back result to the client
    def give_verdict(self, res, username, prob):
        logging.info(res)
        data[username].status[prob] = res
        pickle.dump(data, open('data', 'wb'))
        
        os.system('rm main*')
        
        self.send_response(res)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


    # Handle submissions
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        username = self.parse_data(post_data, 'username\"\r\n\r\n', '\r\n--')
        password = self.parse_data(post_data, 'password\"\r\n\r\n', '\r\n--')
        prob = self.parse_data(post_data, 'problem\"\r\n\r\n', '\r\n--')
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
        while os.path.isfile(str(prob)+'/'+str(tc)+'.in'):
            if lang == 'text/x-c++src':
                ret = os.system('timeout 1 ./main < '+prob+'/'+str(tc)+'.in > out')
            elif lang == 'text/x-python':
                ret = os.system('timeout 1 python main.py < '+prob+'/'+str(tc)+'.in > out')

            if ret == 124:
                self.give_verdict(408, username, prob)
                return
            
            ret = os.system('diff -w out '+prob+'/'+str(tc)+'.out')
            os.system('rm out')

            if ret != 0:
                self.give_verdict(406, username, prob)
                return
            
            tc += 1
        
        self.give_verdict(202, username, prob)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', 6000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()

