FROM ubuntu:latest
ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt install -y make gcc vim python3

WORKDIR /opt/docker/
COPY . /opt/docker/

CMD bash