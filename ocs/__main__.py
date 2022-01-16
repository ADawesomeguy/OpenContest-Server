#!/usr/bin/python

import sys
import os
import logging
from http.server import ThreadingHTTPServer

from ocs.args import args
from ocs.server import server


# Make sure directories exist
if not os.path.isdir(args.data_dir):
    os.makedirs(args.data_dir, exist_ok=True)
if not os.path.isdir(args.contests_dir):
    os.makedirs(args.contests_dir, exist_ok=True)


def main():
    """Run the server"""
    httpd = ThreadingHTTPServer(('localhost', args.port), server)
    logging.info('Starting server')
    httpd.serve_forever()


if __name__ == '__main__':
    sys.exit(main())
