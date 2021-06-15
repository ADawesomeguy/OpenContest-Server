#!/usr/bin/python3

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import logging

logging.basicConfig(filename='log', encoding='utf-8', level=logging.INFO)

class FileUploadRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        logging.info(post_data)

        lang_start = post_data.find('Content-Type: ')
        lang_end = post_data.find('\n', lang_start)
        lang = post_data[lang_start:lang_end].split()[1]
        logging.info(lang)

        program = post_data[lang_end:post_data.rfind('\n----')]
        logging.info(program)

        # Refactor this??
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
            logging.info('Compilation error')
            os.system('rm main*')
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return

        tc = 1
        prob = 1
        while os.path.isfile(str(prob)+'/'+str(tc)+'.in'):
            if lang == 'text/x-c++src':
                ret = os.system('timeout 1 ./main < '+str(prob)+'/'+str(tc)+'.in > out')
            elif lang == 'text/x-python':
                ret = os.system('timeout 1 python main.py < '+str(prob)+'/'+str(tc)+'.in > out')

            if ret == 124:
                logging.info('Timed out')
                os.system('rm main*')
                self.send_response(408)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            
            ret = os.system('diff -w out '+str(prob)+'/'+str(tc)+'.out')
            os.system('rm out')

            if ret != 0:
                logging.info('WA')
                os.system('rm main*')
                self.send_response(406)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            
            tc += 1
        
        logging.info('AC')
        os.system('rm main*')
        self.send_response(202)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', 6000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()

