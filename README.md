# Grader

Reference backend implementation for the [LGP protocol](https://github.com/LadueCS/LGP) written using Python's HTTPServer and SQLite. No external dependencies other than the Python standard library and optionally Firejail for sandboxing.


## Usage

It is highly recommended to put this server behind a reverse proxy like nginx because HTTPServer does not implement any security features.

Also, you should run this server with a sandboxing program. Currently, only Firejail is supported. You can also run this server without a sandbox, but make sure you have some other way of isolating it, such as running it inside a Docker container or virtual machine.

For debugging, you can adjust the logging configuration on the first few lines.

```
usage: grader.py [-h] [-p PORT] [-s SANDBOX]

Reference backend implementation for the LGP protocol

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  which port to run the server on
  -s SANDBOX, --sandbox SANDBOX
                        which sandboxing program to use
```

