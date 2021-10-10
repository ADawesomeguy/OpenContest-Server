#!/usr/bin/python3

import logging
from argparse import ArgumentParser

parser = ArgumentParser(
    description='Reference backend implementation for the LGP protocol')
parser.add_argument('-p', '--port', default=6001,
                    help='which port to run the server on', type=int)
parser.add_argument('-s', '--sandbox', default='firejail',
                    help='which sandboxing program to use', type=str)
parser.add_argument('-d', '--debug', action='store_true',
                    help='run server in debug mode')
args = parser.parse_args()


#logging.basicConfig(filename='log', level=logging.INFO)
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
