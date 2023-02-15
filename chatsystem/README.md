# Chat Server - Team 18

## CS 2510: (Distributed) Computer Operating Systems

This project includes a group chat service that implements a server that is responsible for storing and delivering chats and a client program that enables users to participate in chat groups, exchange messages, and receive messages from other participants. 


## Build Docker Image
`docker build -t chat_system_team_18 .`

## Run Docker Container
`docker run -it chat_system_team_18:latest bash`

## Start the server
`python3 run_chat_server.py`

## Start the client in another terminal
```
docker exec -it docker-container-id bash
python3 run_chat_client_ncurses.py
```

## Team
Arushi Sharma
<br/>
Veerabadra Lokesh

