# OpenContest Server

Reference backend server implementation for the [OpenContest protocol](https://github.com/LadueCS/OpenContest) written using Python's HTTPServer and SQLite. This implementation has no external dependencies other than the Python standard library and systemd and should run on almost all modern Linux distributions.

## Usage

Install the server with `pip`:
```
pip install opencontest-server
```

Run the server with `ocs`. You can place contests like the [sample contest](https://github.com/LadueCS/Test) in a `contests` directory.

For debugging, you can run the server with the `version` flag.

For production usage, you should put this server behind a reverse proxy like nginx because Python's HTTPServer does not implement any security features. You will also need to a domain name and a TLS certificate which you can easily obtain using [Let's Encrypt](https://letsencrypt.org/).
