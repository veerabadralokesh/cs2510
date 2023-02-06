
import logging

class DisplayManager():
    def write(self, *args):
        if len(args) > 0:
            print(*args)
    
    def error(self, *args):
        if len(args) > 0:
            logging.error(*args)
    
    def info(self, *args):
        if len(args) > 0:
            logging.info(*args)
    
    def warn(self, *args):
        if len(args) > 0:
            logging.warn(*args)
    
    def debug(self, *args):
        if len(args) > 0:
            logging.debug(*args)
    
    def read(self, prompt=""):
        return input(prompt)

display_manager = DisplayManager()
