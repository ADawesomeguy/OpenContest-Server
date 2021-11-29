#!/usr/bin/env python3

import logging
import os
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
    def send(self, result):
        if type(result) == int:
            code,body = result, None
        else:
            code,body = result
        logging.debug(code)
        logging.debug(body)
        
        self.send_response(code) # Send status code

        self.send_header('Access-Control-Allow-Origin', '*')

        if body == None:
            self.end_headers()
        else:
            if type(body) == str:
                body = body.encode('utf-8')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body) # Send body
    
    # Process a request
    def process(self, body):
        if 'type' not in body:
            return 400 # Bad request
        if body['type'] not in dir(request):
            return 500 # Not implemented
        
        # Check if all required parameters are in the request
        parameters = str(signature(eval('request.' + body['type'])))[1:-1]
        for parameter in parameters.split():
            if parameter.replace(',', '') not in body:
                return 400 # Bad request

        # Check token
        if 'token' in body:
            authorization = user.authorize_request(body['username'], body['homeserver'], body['token'])
            if not authorization == 200:
                return authorization # Not authorized
        
        # Check if contest exists
        if 'contest' in body:
            if not os.path.isdir(os.path.join(args.contests_dir, body['contest'])):
                return 404 # Contest not found
        
        # Check if problem exists
        if 'problem' in body:
            info = json.load(open(os.path.join(args.contests_dir, body['contest'], 'info.json'), 'r'))
            if body['problem'] not in info['problems'] or datetime.now().timestamp() < datetime.fromisoformat(info['start-time']).timestamp():
                return 404 # Problem not found

        # Run the corresponding function and send the results
        if parameters == '':
            return eval('request.' + body['type'] + '()')
        else:
            return eval('request.' + body['type'] + '(body["' + parameters.replace(', ', '"], body["') + '"])')

    # Handle POST requests
    def do_POST(self):
        # Decode request body
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length).decode('utf-8'))
        logging.debug(body)

        self.send(self.process(body)) # Process request and send back results

# Run the server
server_address = ('localhost', args.port)
httpd = ThreadingHTTPServer(server_address, Server)
logging.info('Starting server')
httpd.serve_forever()
