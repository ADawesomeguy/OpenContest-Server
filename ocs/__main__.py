#!/usr/bin/python

import sys
import logging
from http.server import ThreadingHTTPServer

from ocs.args import args
from ocs.server import server


def main():
    """Run the server"""
    httpd = ThreadingHTTPServer(('localhost', args.port), server)
    logging.info('Starting server')
    httpd.serve_forever()


if __name__ == '__main__':
    sys.exit(main())
