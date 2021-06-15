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


# Save verdict and send back result to the client
def give_verdict(res, server):
    logging.info(res)
    data[username].status[prob] = res
    pickle.dump(data, open('data', 'wb'))
    
    os.system('rm main*')
    
    server.send_response(res)
    server.send_header('Access-Control-Allow-Origin', '*')
    server.end_headers()


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        # Refactor this stuff??
        username_start = post_data.find('username')
        username_end = post_data.find('\r\n----', username_start)
        username = post_data[username_start+13:username_end]
        logging.info(username)

        password_start = post_data.find('password')
        password_end = post_data.find('\r\n----', password_start)
        password = post_data[password_start+13:password_end]
        logging.info(password)

        prob_start = post_data.find('problem')
        prob_end = post_data.find('\r\n----', prob_start)
        prob = post_data[prob_start+12:prob_end]
        logging.info(prob)

        lang_start = post_data.find('Content-Type: ')
        lang_end = post_data.find('\r\n', lang_start)
        lang = post_data[lang_start:lang_end].split()[1]
        logging.info(lang)

        program = post_data[lang_end:post_data.rfind('\r\n----')]
        logging.info(program)
        

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
            give_verdict(500)
            return

        tc = 1
        while os.path.isfile(str(prob)+'/'+str(tc)+'.in'):
            if lang == 'text/x-c++src':
                ret = os.system('timeout 1 ./main < '+prob+'/'+str(tc)+'.in > out')
            elif lang == 'text/x-python':
                ret = os.system('timeout 1 python main.py < '+prob+'/'+str(tc)+'.in > out')

            if ret == 124:
                give_verdict(408)
                return
            
            ret = os.system('diff -w out '+prob+'/'+str(tc)+'.out')
            os.system('rm out')

            if ret != 0:
                give_verdict(406)
                return
            
            tc += 1
        
        give_verdict(202)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', 6000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()

