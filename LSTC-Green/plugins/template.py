# Green Server Plugin Template

import time
import threading

class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {} # Store the user ids and the functions.
        
        self.counter = 0
        self.time = 0
        
        self.running = False # This is needed for a clean shutdown.
    
    def run(self):
        self.running = True
        while self.running: # If False, end the thread.
            time.sleep(0.99)
            self.time += 1
    
    def new_user(self, user_id, functions):
        # Save the functions to self.users
        self.users[user_id] = functions
    
    def lost_user(self, user_id):
        # Delete the user when they disconnect. Free up resources.
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        if message == '+': # Increment the counter.
            self.counter += 1
        
        elif message == 'reset': # Reset the time and counter.
            self.counter = 0
            self.time = 0
        
        elif message == 'update':
            # Send a sensor-update for 'counter' and 'time'.
            self.users[user_id]['sensor-update']('counter',
                                                 self.counter)
            self.users[user_id]['sensor-update']('time', self.time)
    
    def disconnect(self):
        # If the server shuts down, remove all the users.
        for user_id in self.users:
            self.lost_user(user_id)
        
        # This is generally useless, for this plugin, but can be
        # useful in other kinds of plugins.
