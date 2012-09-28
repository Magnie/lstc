# Virtual Space
# By: Magnie

import threading


class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {} # Currently online users.
        
        # 'scratch username' : {'x', 'y', 'd', 'costume', 'shield', 'armor'}
        self.accounts = {}
    
    def run(self):
        # Run any continual scripts here, along side the main server.
        pass
    
    # Messages from server
    
    def new_user(self, user_id, functions):
        self.users[user_id] = User(functions)
    
    def lost_user(self, user_id):
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        pass
    
    def disconnect(self):
        pass


class User(object):
    
    def __init__(self, functions):
        self.functions = functions
        self.account = None
    
    def new_message(message):
        pass
