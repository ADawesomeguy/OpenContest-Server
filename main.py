from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class FileUploadRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Get the size of data
        post_data = self.rfile.read(content_length).decode('ascii') # Get the data itself
        
        print(post_data)

        program = post_data[post_data.find('\n\r\n'):post_data.rfind('\n\r\n')]
        print(program)

        f = open('main.cpp', 'w')
        f.write(program)
        f.close()

        os.system('g++ main.cpp -o main -O2')
        ret = os.system('timeout 1 ./main < in > out')

        os.system('rm main.cpp main')

        if ret == 124:
            print('Timed out')
            return
        
        ret = os.system('diff -w out ans')

        if ret == 0:
            print('AC')
        else:
            print('WA')


        # self._set_response()
        # self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', 6000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run()
