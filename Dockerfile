FROM debian:sid-slim

WORKDIR /usr/src/app

COPY . .

RUN apt update -y
RUN apt install -y ghc python3 python-is-python3 python3-pip nodejs golang wget julia openjdk-17-jdk lua5.4 php ruby rustc mono-mcs
RUN pip install --no-cache-dir requests

CMD [ "python3", "-m", "ocs", "--verbose" ]
