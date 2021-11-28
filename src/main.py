#!/usr/bin/env python3

import logging
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from inspect import signature
from operator import itemgetter
from datetime import datetime

from args import args
import db
import about
import user
import contest

# OpenContest requests
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
    'code': contest.code
}

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

        self.send(*process(body)) # Process request and send back results
    
    # Process a request
    def process(body):
        if 'type' not in body:
            return (400, None) # Bad request
        if body['type'] not in requests:
            return (501, None) # Not implemented
        
        # Check if all required parameters are in the request
        parameters = signature(requests[body['type']])[1:-1]
        try:
            eval(parameters.replace(',', '') + ' = itemgetter(' + parameters + ')(body)')
        except KeyError:
            return (400, None) # Bad request
        
        # Check token
        if token != None:
            authorization = user.authorize_request(username, homeserver, token)
            if not authorization == 200:
                return (authorization, None) # Not authorized
        
        # Check if contest exists
        if contest != None:
            if not os.path.isdir(os.path.join(args.contests_dir, contest)):
                return (404, None) # Contest not found
        
        # Check if problem exists
        if problem != None:
            info = json.load(open(os.path.join(args.contests_dir, contest, 'info.json'), 'r'))
            if problem not in info['problems'] or datetime.now() < datetime.fromisoformat(info['start-time']):
                return (404, None) # Problem not found

        # Run the corresponding function and send the results
        self.send(eval(requests[body['type']] + '(' + parameters + ')'))

# Run the server
server_address = ('localhost', args.port)
httpd = ThreadingHTTPServer(server_address, Server)
logging.info('Starting server')
httpd.serve_forever()
