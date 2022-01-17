# OpenContest Server

An [OpenContest](https://github.com/LadueCS/OpenContest) server written using Python's HTTPServer and SQLite, with no external dependencies other than the Python standard library, [requests](https://docs.python-requests.org/en/latest/), and [Firejail](https://github.com/netblue30/firejail).

## Usage

Install the server with `pip`:
```
pip install opencontest-server
```

Run the server with `ocs`. You can place contests like the [sample contest](https://github.com/LadueCS/Test) in a `contests` directory.

For debugging, you can run the server with `python -m ocs --verbose`

For production usage, you should put this server behind a reverse proxy like nginx because Python's HTTPServer does not implement any security features. You will also need to a domain name and a TLS certificate which you can easily obtain using [Let's Encrypt](https://letsencrypt.org/).
