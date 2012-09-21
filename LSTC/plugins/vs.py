# Virtual Space
# By: Magnie

import threading


class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        
    
    def run(self):
        # Run any continual scripts here, along side the main server.
        pass
    
    # Messages from server
    
    def new_user(self, user_id, functions):
        pass
    
    def lost_user(self, user_id):
        pass
    
    def new_message(self, user_id, message):
        pass
    
    def disconnect(self):
        pass


class User(object):
    
    def __init__(self):
        pass
