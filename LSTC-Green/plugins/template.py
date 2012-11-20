# Green Server Plugin Template

import time
import threading

class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {}
        self.counter = 0
        self.time = 0
        self.running = False # This is needed for a clean shutdown.
    
    def run(self):
        self.running = True
        while self.running:
            time.sleep(0.99)
            self.time += 1
            print self.time
    
    def new_user(self, user_id, functions):
        self.users[user_id] = functions
    
    def lost_user(self, user_id):
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        if message == '+':
            self.counter += 1
        
        elif message == 'reset':
            self.counter = 0
            self.time = 0
        
        elif message == 'update':
            self.users[user_id]['sensor-update']('counter',
                                                 self.counter)
            self.users[user_id]['sensor-update']('time', self.time)
    
    def disconnect(self):
        for user_id in self.users:
            self.lost_user(user_id)
        
        pass
