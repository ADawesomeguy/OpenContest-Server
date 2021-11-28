#!/usr/bin/env python3

import logging
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from args import args
import db
import about
import user
import contest

# Main HTTP server
class Server(BaseHTTPRequestHandler):
    # Send HTTP response
    def send(self, code, body):
        logging.debug(code)
        logging.debug(body)
        
        self.send_response(code) # Send status code

        self.send_header('Access-Control-Allow-Origin', '*')

        if not body == None:
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.wfile.write(body) # Send body
        
        self.end_headers()

    # Handle POST requests
    def do_POST(self):
        # Decode request body
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length).decode('utf-8'))
        logging.debug(body)

        requests = {
            'about': about.about,
            'contests': contest.contests,
            'info': contest.info,
            'problem': contest.problem,
            'solves': contest.solves,
            'register': user.register,
            'authenticate': user.authenticate,
            'authorize': user.authorize,
            'submit': contest.submit,
            'status': contest.status,
            'history': contest.history,
            'code': contest.code,
        }
        # Run the corresponding function and send the results
        self.send(*requests.get(body['type'])(body))

# Run the server
server_address = ('localhost', args.port)
httpd = ThreadingHTTPServer(server_address, Server)
logging.info('Starting server')
httpd.serve_forever()
