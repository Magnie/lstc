# Plugin Template
# By: Magnie

import threading


class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {} # Store online users here.
    
    def run(self):
        # Run any continual scripts here, along side the main server.
        pass
    
    # Messages from server
    
    def new_user(self, user_id, functions):
        self.users[user_id] = User(functions) # Add new user.
    
    def lost_user(self, user_id):
        del self.users[user_id] # Remove dead user.
    
    def new_message(self, user_id, message):
        # Forward $message to the User class.
        self.users[user_id].new_message(message)
    
    def disconnect(self):
        pass

class User(object):
    
    def __init__(self, functions):
        self.functions = functions
        
        # self.send_broadcast('[broadcast]') instead of
        # self.functions['send_broadcast']('[broadcast]')
        self.send_broadcast = self.functions['send_broadcast']
        
        # Same with self.send_sensor. Just shortening the code.
        self.send_sensor = self.functions['send_sensor']
    
    def new_message(self, message):
        
