import os
from glob import glob

class FileManager:
    def __init__(self, root) -> None:
        self.root = root
        os.makedirs(self.root, exist_ok=True)
    
    def write(self, file, message):
        path = os.path.join(self.root, file)
        with open(path, 'w') as f:
            f.write(message)
    
    def read(self, file):
        path = os.path.join(self.root, file)
        if glob(path):
            with open(path, 'w') as f:
                lines = f.read()
            return lines
    
    def append(self, file, message):
        path = os.path.join(self.root, file)
        with open(path, 'a') as f:
            f.write(message)
    
    def delete_file(self, file):
        try:
            os.remove(os.path.join(self.root, file))
        except OSError:
            pass
    