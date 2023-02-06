
from __future__ import print_function

import logging
import grpc
import chat_system_pb2
import chat_system_pb2_grpc

from google.protobuf.json_format import MessageToJson

from client import client_constants

global activity

activity = {

}

def get_user_connection(stub):
    while True:
        try:
            user_id = input("enter username: ")
            status = stub.GetUser(chat_system_pb2.User(user_id=user_id))
            if status.status == True:
                logging.info(f"Login successful with user_id {user_id}")
                activity['active_user_id'] = user_id
                break
            else:
                raise Exception("Login not successful")
        except Exception as ex:
            print(f"Error: {ex}. Please try again.")

def enter_group_chat(stub):
    while True:
        try:
            group_id = activity.get('change_to_group')
            user_id = activity['active_user_id']
            if group_id is None:
                group_id = input("enter group: ")
            else:
                activity['change_to_group'] = None
            group_details = stub.GetGroup(chat_system_pb2.Group(group_id=group_id, user_id=user_id))
            group_data = MessageToJson(group_details)
            if group_details.status == True:
                logging.info(f"Successfully joined group {group_id}")
                activity['active_group_id'] = group_id
                activity['group_data'] = group_data
                break
            else:
                raise Exception("Entering group not successful")
        except Exception as ex:
            print(f"Error: {ex}. Please try again.")


def chat(stub):

    return client_constants.EXIT_CODE


def run():
    status = None
    while True:
        command = input()
        if command.startswith('c '):
            server_string = command[2:].strip()
            if server_string == '':
                server_string = 'localhost:12000'
            try:
                with grpc.insecure_channel(server_string) as channel:
                    stub = chat_system_pb2_grpc.ChatServerStub(channel)
                    get_user_connection(stub)
                    while True:
                        enter_group_chat(stub)
                        status = chat(stub)
                        if status == client_constants.SWITCH_GROUP:
                            continue
                        break
            except grpc.RpcError as rpcError:
                logging.error(f"grpc exception: {rpcError}")
            except Exception as e:
                logging.error(f"Error processing the request, please try again. {e}")
        if status == client_constants.EXIT_CODE:
            break

if __name__ == "__main__":

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    run()
