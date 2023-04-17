# Chat Server p2 - Team 18

## CS 2510: (Distributed) Computer Operating Systems

This project includes a group chat service that implements a server that is responsible for storing and delivering chats and a client program that enables users to participate in chat groups, exchange messages, and receive messages from other participants. Clients can connect to multiple servers and servers sync with each other.

## Docker setup
### Build Docker Image
`docker build -t cs2510_p2 .`

## Using test_p2.py

### Run 5 servers
`python3 test_p2.py init`

### Setting loss rates:
`python test_p2.py loss {server_id1} {server_id2} {loss-rate}`

### Creating partitions:
`python test_p2.py partition 1,2 3,4,5`

### Crashing Server:
`python test_p2.py kill 1`
### Restarting server:
`python test_p2.py relaunch 1`

### Clean up:
`python test_p2.py rm`

### Running client program:
`docker run -it --cap-add=NET_ADMIN --network cs2510 --rm --name cs2510_client1 cs2510_p2 /bin/bash`

## Single container setup
### Run Docker Container
`docker run -it --rm --name cs2510_p2 cs2510_p2:latest bash`

--rm argument tells docker to remove the container as soon as its closed.

### Start the server
`python3 run_chat_server.py -id {id}`

### Start the client in another terminal
```
docker exec -it cs2510_p2 bash
python3 run_chat_client_ncurses.py
```

## Multiple container setup
### Network bride
`docker network create --driver bridge cs2510`

### Run server and client
```
docker run -it --rm --name server --network cs2510 cs2510_p2
docker run -it --rm --name client --network cs2510 cs2510_p2
```
## Multiple hosts setup
### Server
`docker run -it --rm --name server --network host cs2510_p2`
### Client
`docker run -it --rm --name client --network host cs2510_p2`
<!-- ## Application Demo Video
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/PPqlEYtEwCw/0.jpg)](https://www.youtube.com/watch?v=PPqlEYtEwCw) -->


## Team
Arushi Sharma
<br/>
Veerabadra Lokesh

