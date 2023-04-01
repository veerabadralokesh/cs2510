import os
import json
from glob import glob

class FileManager:
    def __init__(self, root) -> None:
        self.root = root
        os.makedirs(self.root, exist_ok=True)
    
    def write(self, file, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        path = os.path.join(self.root, file)
        with open(path, 'w') as f:
            f.write(message)

    def read(self, file):
        path = os.path.join(self.root, file)
        if glob(path):
            with open(path, 'r') as f:
                lines = f.read()
            return lines

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
    
    def delete_file(self, file):
        try:
            os.remove(os.path.join(self.root, file))
        except OSError:
            pass
    
    def list_files(self):
        return os.listdir(self.root)