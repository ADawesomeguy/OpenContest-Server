# grader
Reference backend implementation for the [LGP protocol](https://github.com/LadueCS/LGP) written using Python's HTTPServer.


## Usage

It is highly recommended to put this server behind a reverse proxy like nginx because HTTPServer does not implement any security features.

Also, you must run this server with a sandboxing program. Currently, only Firejail is supported. Although it is possible to run this server without any sandboxing at all, this is extremely dangerous.

```
usage: grader.py [-h] [-p PORT] [-s SANDBOX]

Reference backend implementation for the LGP protocol

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  which port to run the server on
  -s SANDBOX, --sandbox SANDBOX
                        which sandboxing program to use
```

