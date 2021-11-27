#!/usr/bin/env python3

import logging
import os
from argparse import ArgumentParser


parser = ArgumentParser(
    description='Reference server implementation for the OpenContest protocol')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Enable verbose logging')
parser.add_argument('-p', '--port', default=6000,
                    help='Port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail',
                    help='Sandboxing program', type=str)
parser.add_argument('--data-dir', default=os.path.join(os.getcwd(), 'data'),
                    help='Data directory', type=str)
parser.add_argument('--contests-dir', default=os.path.join(os.getcwd(), 'contests'),
                    help='Contests directory', type=str)
parser.add_argument('--problems-dir', default=os.path.join(os.getcwd(), 'problems'),
                    help='Problems directory', type=str)
args = parser.parse_args()


if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
