import threading
import grpc
import chat_system_pb2
import chat_system_pb2_grpc
import server.constants as C

class ServerState:
    def __init__(self, initial={}):
        self._lock = threading.Lock()
        self._state = initial
        self.server_string = '172.30.100.101:12000'

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

class ServerPoolManager:
    def __init__(self, id) -> None:
        """
        id: id of current server
        """
        self.id = id
        self.num_servers = 5
        self.active_stubs = {}

    def connect_to_servers(self):
        states = {}
        for i in range(1, self.num_servers + 1):
            if self.id == i: continue
            state = ServerState()
            states[i] = state
            server_string = state.server_string
            ip_add, port= server_string.split(":")
            self.active_stubs[i] = self.join_server(ip_add[:-1]+f"{str(i)}:" + port, states[i])
        
        return self.active_stubs

    def join_server(self, server_string, state):

        if server_string == state.get(C.SERVER_CONNECTION_STRING):
            print(f'Already connected to server {server_string}')
            return state.get(C.STUB)
        channel = state.get(C.ACTIVE_CHANNEL)

        print(f"Trying to connect to server: {server_string}")
        channel = grpc.insecure_channel(server_string)
        stub = chat_system_pb2_grpc.ChatServerStub(channel)
        server_status = stub.HealthCheck(chat_system_pb2.ActiveSession(session_id=None))
        if server_status.status is True:
            print("Server connection active")
            state[C.ACTIVE_CHANNEL] = channel
            state[C.SERVER_ONLINE] = True
            state[C.SERVER_CONNECTION_STRING] = server_string
            state[C.STUB] = stub
        return stub
