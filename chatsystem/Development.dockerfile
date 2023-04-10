
FROM ubuntu:latest
ENV DEBIAN_FRONTEND noninteractive
ENV USE_DIFFERENT_PORTS 0

RUN apt update && apt install -y make gcc vim python3 python3-pip iproute2 curl

RUN curl -fsSL https://deb.nodesource.com/setup_19.x | bash - &&\
    apt-get install -y nodejs && npm install -g npm && npm install -g nodemon

WORKDIR /opt/docker/
COPY requirements.txt /opt/docker/
RUN python3 -m pip install -r requirements.txt

COPY . /opt/docker/

RUN g++ chat_server.cpp -o chat_server

RUN apt install python-is-python3

CMD bash
