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
    
    log_file = open(fn, 'a+')
    log_file.write('\n[{0}] '.format(strftime('%H:%M:%S')) + data)
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
            self.system_data = {'start': {'links': []}}
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
            time.sleep(0.1)
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
        args = message[1]
        self.users[user_id].new_command(cmd, args)
    
    def disconnect(self):
        """This is usually triggered by the server, it tells the plugin
           to shutdown to make a full shutdown nice and clean."""
        
        # If the server shuts down, remove all the users.
        for user_id in dict(self.users):
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
        self.account_data[name] = {'password': passwd,
                                   'data': data}
        
        # Come on, who wouldn't want to save their account after
        # it's been created?
        self.save_all()
    
    def ship_data(self, name):
        """Getter function for retreiving ship data."""
        
        return self.account_data[name]['data']
        
    def get_universe(self):
        """Returns a universe with an open spot for a player to join."""
        
        for uni in self.universes:
            spot = uni.spot_open() # Get the spot number/id
            if spot: # If it's not False, then return it.
                return uni, spot
        
        return False, None # No space available


class Universe(object):
    
    def __init__(self):
        self.max_ships = 12
        self.max_bullets = 12
        
        self.ships = {}
        for x in xrange(1, self.max_ships):
            self.ships['s' + str(x)] = None
        
        self.bullets = {}
        for x in xrange(1, self.max_bullets):
            self.bullets['b' + str(x)] = None
    
    def spot_open(self):
        """Check if a spot is available in the universe"""
        for x in self.ships:
            print self.ships[x]
            if not self.ships[x]: # (if self.ships[x] == None)
                return x
        
        return False
    
    def update(self):
        """Update the universe"""
    
        # Test for collisions
        for bullet in self.bullets:
            for ship in self.ships:
                pass
    
        # Update objects in motion
        for ship_id in self.ships:
            ship = self.ships[ship_id]
            if ship:
                ship.update()
        
        for bullet in self.bullets:
            pass
    
    def new_ship(self, ship_id, ship):
        self.ships[ship_id] = ship
    
    def get_objects(self, ship_id):
        ship = self.ships[ship_id]
        
        objects = {'ships': self.ships,
                   'bullets': self.bullets,
                   'planets': None}
        return objects
    
    def remove(self, ship_id):
        self.ships[ship_id] = None
        self.bullets[ship_id] = None


class Client(object):
    
    def __init__(self, server, functions):
        self.server = server
        self.functions = functions
        
        self.send_sensor = functions['sensor-update']
        self.send_broadcast = functions['broadcast']
        
        self.logged_in = False
        
        self.ship = None
    
    def new_command(self, cmd, args):
        if self.logged_in:
            self.ship.new_action(cmd, args)
        
        else:
            if cmd == 'login':
                name, passwd = args.split(' ', 1)
                if self.server.check_account(name, passwd):
                    universe, ship_id = self.server.get_universe()
                    
                    if universe:
                        self.logged_in = True
                        data = self.server.ship_data(name)
                        self.ship = Ship(universe, ship_id, data,
                                         self.functions['sensor-update'],
                                         self.functions['broadcast'])
                        self.send_sensor('login status', 'logged in')
                    
                    else:
                        self.send_sensor('login status', 'no universe')
                
                else:
                    self.send_sensor('login status', 'login fail')
                
            
            elif cmd == 'register':
                name, passwd = args.split(' ', 1)
                self.server.new_account(name, passwd)
                self.send_sensor('login status', 'registered')
            
            elif cmd == 'admin':
                # Some admin panel?
                pass
        
    def disconnect(self):
        if self.ship:
            self.ship.disconnect()


class Ship(object):
    
    def __init__(self, universe, ship_id, data, sensor, broadcast):
        self.universe = universe
        self.send_sensor = sensor
        self.send_broadcast = broadcast
        self.ship_id = ship_id
        
        self.universe.new_ship(self.ship_id, self)
        
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
        self.accel = 0.2
        self.max_speed = 5
        
        # Velocities
        self.x_vel = 0
        self.y_vel = 0
        
        self.thrust = False
        self.thrust_1 = 0
        self.turn_left = False
        self.turn_left_1 = 0
        self.turn_right = False
        self.turn_right_1 = 0
        
        # Other
        self.frame = 0
    
    def disconnect(self):
        self.universe.remove(self.ship_id)
    
    def new_action(self, cmd, args):
        if cmd == 'thrust':
            self.thrust = True
            self.thrust_1 = 1
        
        elif cmd == 'nothrust':
            self.thrust = False
        
        elif cmd == 'left':
            self.turn_left = True
            self.turn_left_1 = 1
        
        elif cmd == 'noleft':
            self.turn_left = False
        
        elif cmd == 'right':
            self.turn_right = True
            self.turn_right_1 = 1
        
        elif cmd == 'noright':
            self.turn_right = False
        
        elif cmd == 'getid':
            self.send_sensor('your id', self.ship_id)
            self.send_broadcast('id sent')
        
        elif cmd == 'getall':
            objects = self.universe.get_objects(self.ship_id)
            ships = objects['ships']
            bullets = objects['bullets']
            planets = objects['planets']
            
            for ship_id in ships:
                name = ship_id
                if not ships[ship_id]:
                    self.send_sensor(name + 'x', '0')
                    self.send_sensor(name + 'xv', '0')
                    self.send_sensor(name + 'y', '0')
                    self.send_sensor(name + 'yv', '0')
                    self.send_sensor(name + 'd', '0')
                    self.send_sensor(name + 'dt', '0')
                    continue
                
                ship = ships[ship_id]
                
                self.send_sensor(name + 'x', ship.x_pos)
                self.send_sensor(name + 'xv', ship.x_vel)
                self.send_sensor(name + 'y', ship.y_pos)
                self.send_sensor(name + 'yv', ship.y_vel)
                self.send_sensor(name + 'd', ship.dir)
                self.send_sensor(name + 'dt',
                                 ship.turn_left or ship.turn_right)
            
            self.frame = (self.frame + 1) % 2
            self.send_sensor('frame', self.frame)
    
    def update(self):
        if self.thrust or self.thrust_1:
            self.thrust_1 = 0
            
            radians = (math.pi / 180) * (self.dir + 180)
            xin = math.sin(radians) * self.accel
            yin = math.cos(radians) * self.accel
            if abs(self.x_vel + xin) < self.max_speed:
                self.x_vel += xin
            
            if abs(self.y_vel + yin) < self.max_speed:
                self.y_vel += yin
        
        if self.turn_left or self.turn_left_1:
            self.dir -= 15
            self.turn_left_1 = 0
        
        if self.turn_right or self.turn_right_1:
            self.dir += 15
            self.turn_right_1 = 0
        
        if self.dir > 360:
            self.dir -= 360
        
        elif self.dir < 0:
            self.dir += 360
        
        self.x_pos += self.x_vel
        self.y_pos += self.y_vel
        
        #print '{0}x {1}y {2}d'.format(self.x_pos, self.y_pos, self.dir)
    
    def in_range(self, x, y, radius):
        dist = (x - self.x_pos ** 2) + ((y - self.y_pos) ** 2)
        if dist < radius:
            return True
        
        return False
        
