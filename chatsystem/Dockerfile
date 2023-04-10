FROM ubuntu:latest
ENV DEBIAN_FRONTEND noninteractive
ENV USE_DIFFERENT_PORTS 0

RUN apt update && apt install -y make gcc vim python3 python3-pip iproute2 python-is-python3

WORKDIR /opt/docker/
COPY requirements.txt /opt/docker/
RUN python3 -m pip install -r requirements.txt

COPY . /opt/docker/

RUN g++ chat_server.cpp -o chat_server

CMD bash