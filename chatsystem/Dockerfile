FROM ubuntu:latest
ENV DEBIAN_FRONTEND noninteractive
ENV USE_DIFFERENT_PORTS 0

RUN apt update && apt install -y make gcc vim python3 python3-pip

WORKDIR /opt/docker/
COPY . /opt/docker/

RUN python3 -m pip install -r requirements.txt

RUN g++ chat_server.cpp -o chat_server

CMD bash