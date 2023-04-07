import os
import json
from glob import glob

class FileManager:
    def __init__(self, root) -> None:
        self.root = root
        self.fast_root = os.path.join(root, "cache")
        os.makedirs(self.root, exist_ok=True)
    
    def write(self, file, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        path = os.path.join(self.root, file)
        with open(path, 'w') as f:
            f.write(message)
    
    def fast_write(self, file, message: bytes):
        try:
            path = os.path.join(self.fast_root, file)
            file_desc = os.open(path, os.O_RDWR | os.O_CREAT)
            os.write(file_desc, message)     
            os.close(file_desc)
        except Exception as e:
            print(f'Error in fast_write: {e}')

    def read(self, file):
        path = os.path.join(self.root, file)
        if glob(path):
            with open(path, 'r') as f:
                lines = f.read()
            return lines
    
    def fast_read(self, file) -> bytes:
        try:
            path = os.path.join(self.fast_root, file)
            file_size = os.path.getsize(path)
            file_desc = os.open(path, os.O_RDONLY)
            lines = os.read(file_desc, file_size)
            os.close(file_desc)
            return lines
        except Exception as e:
            print(f'Error in fast_read: {e}')

    def readlines(self, file):
        path = os.path.join(self.root, file)
        if glob(path):
            with open(path, 'r') as f:
                lines = f.readlines()
            return lines
    
    def append(self, file, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        path = os.path.join(self.root, file)
        with open(path, 'a') as f:
            f.write(message)
            f.write('\n')
    
    def delete_file(self, file, fast=False):
        try:
            if fast:
                os.remove(os.path.join(self.fast_root, file))
            else:
                os.remove(os.path.join(self.root, file))
        except OSError:
            pass
    
    def list_files(self, fast=False):
        if fast:
            return os.fast_root
        return os.listdir(self.root)