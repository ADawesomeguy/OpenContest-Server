# OpenContest Server

Reference backend server implementation for the [OpenContest protocol](https://github.com/LadueCS/OpenContest) written using Python's HTTPServer and SQLite. No external dependencies other than the Python standard library and optionally Firejail for sandboxing.


## Usage

Install the server with `pip` or clone this repository. Run the server with `ocs` or `src/main.py`. You can place contests like the [sample contest](https://github.com/LadueCS/Test) in a `contests` directory.

It is highly recommended to put this server behind a reverse proxy like nginx because HTTPServer does not implement any security features.

For debugging, you can run the server with the `version` flag.
