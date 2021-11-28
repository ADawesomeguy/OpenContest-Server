# OpenContest Server

Reference backend server implementation for the [OpenContest protocol](https://github.com/LadueCS/OpenContest) written using Python's HTTPServer and SQLite. No external dependencies other than the Python standard library and optionally Firejail for sandboxing.


## Usage

Run the server with `src/main.py`. You can place contests like the [sample contest](https://github.com/LadueCS/Test) in a `contests` directory.

It is highly recommended to put this server behind a reverse proxy like nginx because HTTPServer does not implement any security features.

Also, you should run this server with a sandboxing program. Currently, only Firejail is supported. You can also run this server without a sandbox, but make sure you have some other way of isolating it, such as running it inside a Docker container or virtual machine.

For debugging, you can run the server with the `version` flag.

```
usage: main.py [-h] [-v] [-p PORT] [-s SANDBOX] [-d DATA_DIR] [-c CONTESTS_DIR]

Reference server implementation for the OpenContest protocol

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose logging
  -p PORT, --port PORT  Port to run the server on
  -s SANDBOX, --sandbox SANDBOX
                        Sandboxing program
  -d DATA_DIR, --data-dir DATA_DIR
                        Data directory
  -c CONTESTS_DIR, --contests-dir CONTESTS_DIR
                        Contests directory
```

