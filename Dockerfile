FROM docker.io/debian:sid-slim

WORKDIR /usr/src/app

COPY . .

RUN apt-get update -y
RUN apt-get install -y ghc python3 python-is-python3 python3-requests nodejs golang wget julia openjdk-17-jdk lua5.4 php ruby rustc mono-mcs
RUN apt-get clean

CMD [ "python3", "-m", "ocs", "--verbose" ]
