FROM ubuntu:24.04

RUN apt update && \
    apt install -y squid

COPY squid.conf /etc/squid/squid.conf

CMD ["squid", "-N"]