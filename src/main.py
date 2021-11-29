#!/usr/bin/env python3

import logging
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from inspect import signature
from operator import itemgetter
from datetime import datetime

from args import args
import request

# Main HTTP server
class Server(BaseHTTPRequestHandler):
    # Send HTTP response
    def send(self, code, body=None):
        logging.debug(code)
        logging.debug(body)
        
        self.send_response(code) # Send status code

        self.send_header('Access-Control-Allow-Origin', '*')

        if not body == None:
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode('utf-8')) # Send body
        else:
            self.end_headers()
        

    # Process a request
    def process(self, body):
        if 'type' not in body:
            return (400, None) # Bad request
        if body['type'] not in dir(request):
            return (501, None) # Not implemented
        
        # Check if all required parameters are in the request
        parameters = str(signature(eval('request.' + body['type'])))[1:-1]
        if parameters != '':
            try:
                eval(parameters.replace(',', '') + ' = itemgetter(' + parameters + ')(body)')
            except KeyError:
                return (400, None) # Bad request
        
        # Check token
        if 'token' in vars():
            authorization = user.authorize_request(username, homeserver, token)
            if not authorization == 200:
                return (authorization, None) # Not authorized
        
        # Check if contest exists
        if 'contest' in vars():
            if not os.path.isdir(os.path.join(args.contests_dir, contest)):
                return (404, None) # Contest not found
        
        # Check if problem exists
        if 'problem' in vars():
            info = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))
            if problem not in info['problems'] or datetime.now() < datetime.fromisoformat(info['start-time']):
                return (404, None) # Problem not found

        # Run the corresponding function and send the results
        return eval('request.' + body['type'] + '(' + parameters + ')')

    # Handle POST requests
    def do_POST(self):
        # Decode request body
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length).decode('utf-8'))
        logging.debug(body)

        self.send(*self.process(body)) # Process request and send back results

# Run the server
server_address = ('localhost', args.port)
httpd = ThreadingHTTPServer(server_address, Server)
logging.info('Starting server')
httpd.serve_forever()
