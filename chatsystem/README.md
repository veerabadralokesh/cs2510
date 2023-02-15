# Chat Server - Team 18

## CS 2510: (Distributed) Computer Operating Systems

This project includes a group chat service that implements a server that is responsible for storing and delivering chats and a client program that enables users to participate in chat groups, exchange messages, and receive messages from other participants. 

## Docker setup
### Build Docker Image
`docker build -t chat_system_team_18 .`

## Single container setup
### Run Docker Container
`docker run -it --rm --name chat_system_team_18 chat_system_team_18:latest bash`

--rm argument tells docker to remove the container as soon as its closed.

### Start the server
`python3 run_chat_server.py`

### Start the client in another terminal
```
docker exec -it chat_system_team_18 bash
python3 run_chat_client_ncurses.py
```

## Multiple container setup
### Network bride
`docker network create --driver bridge cs2510`

### Run server and client
```
docker run -it --rm --name server --network cs2510 chat_system_team_18
docker run -it --rm --name client --network cs2510 chat_system_team_18
```
## Multiple hosts setup
### Server
`docker run -it --rm --name server --network host chat_system_team_18`
### Client
`docker run -it --rm --name client --network host chat_system_team_18`
## Application Demo Video
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/PPqlEYtEwCw/0.jpg)](https://www.youtube.com/watch?v=PPqlEYtEwCw)


## Team
Arushi Sharma
<br/>
Veerabadra Lokesh

