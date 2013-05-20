# Galactic Space Multiplayer Game

import time
import threading
import cPickle
import math
import os


DIRECTORY = 'galactic' # Folder to save files and data

def save_data(fn, data):
    fn = os.path.join(DIRECTORY, fn)
    data_file = open(fn, 'w')
    cPickle.dump(data, data_file)
    data_file.close()

def load_data(fn):
    fn = os.path.join(DIRECTORY, fn)
    try:
        data_file = open(fn, 'r')
        data = cPickle.load(data_file)
        data_file.close()
        return data
    
    except IOError, e:
        data_file = open(fn, 'w')
        data_file.close()
        return False

def save_log(fn, data):
    fn = os.path.join(DIRECTORY, fn)
    if isinstance(data, list):
        data = '\n'.join(data)
    
    log_file = open(fn, 'w')
    log_file.write(data)
    log_file.close()

def append_log(fn, data):
    fn = os.path.join(DIRECTORY, fn)
    if isinstance(data, list):
        data = '\n'.join(data)
    
    log_file = open(fn, 'w+')
    log_file.writeline(data)
    log_file.close()

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

ensure_dir(DIRECTORY)

class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {} # Store the user ids and the functions.
        self.num_universes = 3 # Create this number of instances
        
        # Load account data, if it doesn't exist, create it. :)
        self.account_data = load_data('accounts.txt')
        if not self.account_data:
            self.account_data = {}
            # 'username' : {'password': 'pass123', 'data': {data here}}
            self.new_account('root', 'root123')
            
            save_data('accounts.txt', self.account_data)
        
        # Load system/universe data, if it doesn't exist, create it. :)
        self.system_data = load_data('systems.txt')
        if not self.system_data:
            self.system_data = {}
            # 'system' : {data here}
            save_data('systems.txt', self.system_data)
        
        # Create the instances
        self.universes = []
        for x in xrange(1, self.num_universes):
            self.universes.append(Universe())
            
        
        self.running = False # This is needed for a clean shutdown.
        
    
    def run(self):
        """This is the clock of the server, updates everything at 10 frames
           per second."""
        
        self.running = True
        while self.running: # If False, end the thread.
            time.sleep(0.9999)
            for uni in self.universes:
                uni.update()
    
    def new_user(self, user_id, functions):
        """The handler for a new client for the server."""
        
        # Save the functions to self.users
        self.users[user_id] = Client(self, functions)
    
    def lost_user(self, user_id):
        """If for whatever reason a client disconnects, this will be
           triggered."""
        
        # Delete the user when they disconnect. Free up resources.
        
        if user_id in self.users:
            self.users[user_id].disconnect()
            del self.users[user_id]
    
    def new_message(self, user_id, message):
        """When a message is sent from a client, send it to the appopriate
           class object for parsing."""
        
        message = message.split(':', 1)
        cmd = message[0]
        args = message[1].split(';')
        self.users[user_id].new_command(cmd, args)
    
    def disconnect(self):
        """This is usually triggered by the server, it tells the plugin
           to shutdown to make a full shutdown nice and clean."""
        
        # If the server shuts down, remove all the users.
        for user_id in self.users:
            self.lost_user(user_id)
        
        self.running = False
        save_data('accounts.txt', self.account_data)
    
    # Other stuff
    def save_all(self):
        """Global save for any modified data."""
        
        save_data('accounts.txt', self.account_data)
        save_data('systems.txt', self.system_data)
    
    def check_account(self, name, passwd):
        """Check if the account exists and the password is correct."""
        
        if name in self.account_data:
            if passwd == self.account_data[name]['password']:
                return True
        
        return False
    
    def new_account(self, name, passwd):
        """Creates a new account if it's not already created."""
        
        if name in self.account_data:
            return False
        
        # All the data for the ship.
        data = {}
        data['x'] = 0
        data['y'] = 0
        data['dir'] = 0
        data['system'] = 'start'
        data['last'] = 'Home'
        data['type'] = 'shuttle'
        data['hp'] = 50
        data['shield'] = 50
        
        # The actual account
        self.account_data[name]['password'] = passwd
        self.account_data[name]['data'] = data
        
        # Come on, who wouldn't want to save their account after
        # it's been created?
        self.save_all()
    
    def ship_data(self, name):
        """Getter function for retreiving ship data."""
        
        return self.account_data[name]['data']
        
    def get_universe(self):
        """Returns a universe with an open spot for a player to join."""
        
        for uni in self.universes:
            if uni.spot_open():
                return uni
        
        return False


class Universe(object):
    
    def __init__(self):
        self.max_ships = 12
        self.max_bullets = 12
        
        self.ships = {}
        for x in xrange(1, self.max_ships):
            self.ships[str(x)] = None
        
        self.bullets = {}
        for x in xrange(1, self.max_bullets):
            self.bullets[str(x)] = None
    
    def spot_open(self):
        """Check if a spot is available in the universe"""
        for x in self.ships:
            if not x:
                return True
        
        return False
    
    def update(self):
        """Update the universe"""
    
        # Test for collisions
        for bullet in self.bullets:
            for ship in self.ships:
                pass
    
        # Update objects in motion
        for ship in self.ships:
            pass
        
        for bullet in self.bullets:
            pass


class Client(object):
    
    def __init__(self, server, functions):
        self.server = server
        self.functions = functions
        
        self.logged_in = False
        
        self.ship = None
    
    def new_command(cmd, args):
        if self.logged_in:
            self.ship.new_action(cmd, args)
        
        else:
            if cmd == 'login':
                name, passwd = args.split(' ', 1)
                if self.server.check_account(name, passwd):
                    universe = self.server.get_universe()
                    
                    if universe:
                        self.logged_in = True
                        data = self.server.ship_data(name)
                        self.ship = Ship(universe, data,
                                         self.functions['sensor-update'],
                                         self.functions['broadcast'])
            
            elif cmd == 'register':
                name, passwd = args.split(' ', 1)
                self.server.new_account(name, passwd)
            
            elif cmd == 'admin':
                # Some admin panel?
                pass


class Ship(object):
    
    def __init__(self, universe, data, sensor, broadcast):
        self.universe = universe
        self.send_sensor = sensor
        self.send_broadcast = broadcast
        
        # Ship Location
        self.system = data['system']
        self.x_pos = data['x']
        self.y_pos = data['y']
        self.dir = data['dir']
        
        # Ship Attributes
        self.ship_type = data['type']
        self.ship_life = data['hp']
        self.ship_shield = data['shield']
        self.last_planet = data['last']
        
        # Velocities
        self.x_vel = 0
        self.y_vel = 0
    
    def new_action(self, cmd, args):
        if cmd == 'thrust':
            pass
        
        elif cmd == 'left':
            pass
        
        elif cmd == 'right':
            pass
    
    def update(self):
        pass
        
