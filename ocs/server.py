import logging
from json import loads
from http.server import BaseHTTPRequestHandler
from inspect import signature
from datetime import datetime

import ocs.request
from ocs.data import about_data, contest_data
from ocs.user import authorize_request


class server(BaseHTTPRequestHandler):
    """Main HTTP server"""

    def send(self, result):
        """Send HTTP response"""
        if isinstance(result, int):
            code, body = result, None
        else:
            code, body = result
        logging.debug(code)
        logging.debug(body)

        self.send_response(code)  # Send status code
        self.send_header('Access-Control-Allow-Origin', '*')
        if body is None:
            self.end_headers()
        else:
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)  # Send body

    def process(self, body):
        """Process a request"""

        if 'type' not in body:
            return 400  # Bad request
        if body['type'] not in dir(ocs.request):
            return 500  # Not implemented

        # Check if all required parameters are in the request
        parameters = str(signature(eval('ocs.request.' + body['type'])))[1:-1]
        for parameter in parameters.split():
            if 'None' in parameter:  # Optional parameter
                if parameter.replace('=None', '') not in body:
                    parameters = parameters.replace(', ' + parameter, '')  # Remove it
                else:
                    parameters = parameters.replace('=None', '')
            else:
                if parameter.replace(',', '') not in body:
                    return 400  # Bad request

        # Check token
        if 'token' in body and not body['type'] == 'authorize':
            authorization = authorize_request(body['username'], body['homeserver'], body['token'])
            if not authorization == 200:
                return authorization  # Not authorized

        # Check if contest exists
        if 'contest' in body and body['contest'] not in about_data['contests']:
            return 404  # Contest not found

        # Check if problem exists
        if 'problem' in body and (body['problem'] not in contest_data[body['contest']]['problems'] or
            datetime.now().timestamp() < datetime.fromisoformat(contest_data[body['contest']]['start-time']).timestamp()):
            return 404  # Problem not found

        # Run the corresponding function and send the results
        if parameters == '':
            return eval('ocs.request.' + body['type'] + '()')
        else:
            return eval('ocs.request.' + body['type'] + '(body["' + parameters.replace(', ', '"], body["') + '"])')

    def do_OPTIONS(self):
        """Handle CORS"""

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()

    def do_POST(self):
        """Handle POST requests"""

        # Decode request body
        content_length = int(self.headers['Content-Length'])
        body = loads(self.rfile.read(content_length).decode('utf-8'))
        logging.debug(body)

        self.send(self.process(body))  # Process request and send back results
