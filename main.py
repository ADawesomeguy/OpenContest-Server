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
        ret = os.system('g++ main.cpp -o main -O2')

        if ret:
            print('Compilation error')
            os.system('rm main.cpp')
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return

        tc = 1
        prob = 1
        while os.path.isfile(str(prob)+'/'+str(tc)+'.in'):
            os.system('rm out')
            ret = os.system('timeout 1 ./main < '+str(prob)+'/'+str(tc)+'.in > out')

            if ret == 124:
                print('Timed out')
                os.system('rm main.cpp main')
                self.send_response(408)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            
            ret = os.system('diff -w out '+str(prob)+'/'+str(tc)+'.out')

            if ret != 0:
                print('WA')
                os.system('rm main.cpp main')
                self.send_response(406)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            
            tc += 1
        
        print('AC')
        os.system('rm main.cpp main')
        self.send_response(202)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


def run(server_class=HTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('127.0.0.1', 6000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()

