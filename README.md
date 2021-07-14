# LGP-Server

Reference backend server implementation for the [LGP protocol](https://github.com/LadueCS/LGP) written using Python's HTTPServer and SQLite. No external dependencies other than the Python standard library and optionally Firejail for sandboxing.


## Usage

Run the server with `./main.py`. You can place contests like the [sample contest](https://github.com/LadueCS/Test) in a `contests` directory.

It is highly recommended to put this server behind a reverse proxy like nginx because HTTPServer does not implement any security features.

Also, you should run this server with a sandboxing program. Currently, only Firejail is supported. You can also run this server without a sandbox, but make sure you have some other way of isolating it, such as running it inside a Docker container or virtual machine.

For debugging, you can run the server with the `debug` flag.

```
usage: main.py [-h] [-p PORT] [-s SANDBOX] [-d]

Reference backend implementation for the LGP protocol

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  which port to run the server on
  -s SANDBOX, --sandbox SANDBOX
                        which sandboxing program to use
  -d, --debug           run server in debug mode
```

