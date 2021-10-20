#!/usr/bin/env python3

import logging
import json
from base64 import b64decode
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from args import args
import user
import contest
from var import cwd

tokenKey = 'tokenKey123'  # TODO: hide token key


def about(_=None):  # Return info about server
    return open(cwd+'about.json', 'r').read()


class FileUploadRequestHandler(BaseHTTPRequestHandler):
    def send(self, body, code=200):
        logging.info(body)
        if type(body) == tuple:  # Send status code with response body
            self.send(*body)
        elif type(body) == int:  # Send status code without response body
            self.send_response(body)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:  # Send response body
            try:
                body = json.loads(body)
            except (TypeError, json.decoder.JSONDecodeError):
                pass
            body = json.dumps(body).encode('utf-8')
            self.send_response(code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Contest-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body)

    def parse_headers(self):
        try:
            auth, auth_content = self.headers['Authorization'].split(' ', 1)
            if auth == 'Basic':
                username, password = b64decode(
                    auth_content).decode('utf-8').split(':', 1)
                return {'username': username, 'password': password}
            elif auth == 'Bearer':
                return {'token': auth_content}
        except Exception:
            return {}

    def parse_data(self):
        try:
            # Get the size of data
            content_length = int(self.headers['Content-Length'])
            return json.loads(self.rfile.read(content_length).decode(
                'ascii'))  # Get the data itself
        except Exception:
            return {}

    def do_OPTIONS(self):  # Handle POST requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'Authorization, Content-Type')
        self.end_headers()

    def do_POST(self):
        self.handle_request()

    def do_GET(self):
        self.handle_request()

    def handle_request(self):  # Handle requests
        command, path, data, auth = self.command, self.path, self.parse_data(), self.parse_headers()
        logging.info(data)
        data.update(auth)
        print(command, path, data)

        routes = {
            'POST': {  # POST Requests
                '/user/register': user.register,
                '/contest/submit': contest.submit,
            },
            'GET': {  # GET Requests
                '/about': about,
                '/user/login': user.login,
                '/contest': contest.contests,
                '/contest/info': contest.info,
                '/contest/problems': contest.problems,
                '/contest/solves': contest.solves,
                '/contets/status': contest.status
            }
        }
        self.send(routes.get(command, {}).get(
            path.rstrip('/'), lambda _: 400)(data))


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
