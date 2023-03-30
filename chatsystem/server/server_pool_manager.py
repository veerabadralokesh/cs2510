import threading
from time import sleep
import grpc
import chat_system_pb2
import chat_system_pb2_grpc
import server.constants as C

class ServerState:
    def __init__(self, initial={}):
        self._lock = threading.Lock()
        self._state = initial

    def __setitem__(self, key, value):
        with self._lock:
            self._state[key] = value

    def __getitem__(self, key):
        return self._state[key]

    def __contains__(self, key):
        return (key in self._state)

    def __str__(self) -> str:
        return self._state.__str__()

    def get(self, key):
        return self._state.get(key)
    
    def get_dict(self):
        return self._state

def connect_to_servers(active_stubs, num_servers, id):
    while len(active_stubs) < num_servers-1:
        for i in range(1, num_servers + 1):
            try:
                if id == i or active_stubs.get(i) is not None: 
                    continue
                if C.USE_DIFFERENT_PORTS:
                    server_string = f'localhost:{(11999+i)}'
                else:
                    server_string = C.SERVER_STRING.format(i)
                stub = join_server(server_string)
                if stub:
                    active_stubs[i] = stub

            except Exception:
                pass
        sleep(C.CONNECT_SERVER_INTERVAL)

class ServerPoolManager:
    def __init__(self, id) -> None:
        """
        id: id of current server
        """
        self.id = id
        self.num_servers = 5
        self.active_stubs = {}
        t = threading.Thread(target=connect_to_servers, 
                             daemon=True, 
                             args=[self.active_stubs, self.num_servers, self.id])
        t.start()
    
    def get_connected_servers_view(self):
        return sorted(self.active_stubs.keys())


def join_server(server_string):
    print(f"Trying to connect to server: {server_string}")
    channel = grpc.insecure_channel(server_string)
    stub = chat_system_pb2_grpc.ChatServerStub(channel)
    server_status = stub.Ping(chat_system_pb2.BlankMessage())
    if server_status.status is True:
        print(f"Connected to server: {server_string}")
        return stub
