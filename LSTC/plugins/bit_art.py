# Bit Art
# Server By: Magnie
# Original Idea By: Molybdenum - http://scratch.mit.edu/users/Molybdenum

# Todo: Fix saving.

import threading
import time
import cPickle


class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.art = {'0': {'0': 1}} # self.art[x][y] = 0 or 1
        
        
        self.users = {} # Connected users: id : functions
        self.placers = [] # Allowed to place.
        self.banned = [] # [Scratch Name]
        self.old_art = None
        self.time = 0
        
        self.last_placer = 'no one'
        self.size = 6
        
        self.column_structure = '1234567890-=qwertyuiopasdfghjklzxcvbnm!@#$%^&*()_+{}|:"<>?~`'
        
        self.switch = 0
        
        self.load_image()
    
    def run(self):
        # Run any continual scripts here, along side the main server.
        return
        while True:
            time.sleep(60)
            print 'Saving image.'
            if self.old_art != self.art:
                self.save_image()
                self.old_art = self.art
    
    # Messages from server
    
    def new_user(self, user_id, functions):
        self.users[user_id] = functions
        self.update_whole(user_id)
    
    def lost_user(self, user_id):
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        message = message.split(' ')
        cmd = message[0]
        
        if len(message) > 1:
            args = message[1:]
        
        else:
            args = None
        
        if cmd == 'update' and len(args) == 2:
            self.update_pixel(args[0], args[1], user_id)
        
        elif cmd == 'login' and len(args) == 2:
            self.scratch_auth(args[0], args[1], user_id)
        
        elif cmd == 'reset_map' and args[0] == '1234':
            self.reset_map()
    
    def disconnect(self):
        pass
        # self.save_image()
    
    
    # Saving/Loading Image
    
    def load_image(self, name='bit.txt'):
        try:
            art_file = open(name, 'r')
            self.art = {}
            self.art = cPickle.load(art_file)
            art_file.close()
        
        except IOError, e:
            print e
            art_file = open(name, 'w')
            cPickle.dump(self.art, art_file)
            art_file.close()
    
    def save_image(self, name='bit.txt'):
        art_file = open(name, 'w')
        cPickle.dump(self.art, art_file)
        art_file.close()
    
    def check_last(self):
        # Check if the last time it saved was over 60 seconds.
        if time.time() > (self.time):
            if self.old_art != self.art:
                self.save_image()
                self.old_art = self.art
            
            self.time = time.time() + 60
    
    # Game functions
    
    def update_pixel(self, pos_x, pos_y, uid):
        #if uid not in self.placers:
        #    return
        
        pos_x = self.size * round(pos_x / float(size))
        pos_y = self.size * round(pos_y / float(size))
        
        if pos_y not in self.art:
            self.art[pos_y] = {}
        
        if pos_x not in self.art[pos_y]:
            self.art[pos_y][pos_x] = 0
        
        # Toggle the pixel.
        value = self.art[pos_y][pos_x]
        value = (value + 1) % 2
        
        self.art[pos_y][pos_x] = value
        self.last_placer = uid
        
        self.update_clients(pos_x, pos_y, value)
        
        self.check_last()
        
    def update_clients(self, pos_x, pos_y, value):
        x = pos_x
        y = pos_y
        # Update the value of [x][y] pixel.
        for user_id in self.users:
            user = self.users[user_id]
            user['send_sensor']('last', self.last_placer)
            if self.switch == 0:
                user['send_sensor']('x0', str(x))
                user['send_sensor']('y0', str(y))
                user['send_sensor']('value0', str(value))
                user['send_broadcast']('pixel_update0')
                self.switch = 1
                    
            elif self.switch == 1:
                user['send_sensor']('x1', str(x))
                user['send_sensor']('y1', str(y))
                user['send_sensor']('value1', str(value))
                user['send_broadcast']('pixel_update1')
                self.switch = 2
                    
            elif self.switch == 2:
                user['send_sensor']('x2', str(x))
                user['send_sensor']('y2', str(y))
                user['send_sensor']('value2', str(value))
                user['send_broadcast']('pixel_update2')
                self.switch = 0
    
    def update_whole(self, user_id):
        # Send the entire map to the client.
        switch = 0
        
        user = self.users[user_id]
        user['send_sensor']('value0', '1')
        user['send_sensor']('value1', '1')
        user['send_sensor']('value2', '1')
        user['send_broadcast']('reset_map')
        for y in self.art:
            for x in self.art[y]:
                if self.art[y][x] != 0:
                    if switch == 0:
                        user['send_sensor']('x0', str(x))
                        user['send_sensor']('y0', str(y))
                        user['send_broadcast']('pixel_update0')
                        switch = 1
                    
                    elif switch == 1:
                        user['send_sensor']('x1', str(x))
                        user['send_sensor']('y1', str(y))
                        user['send_broadcast']('pixel_update1')
                        switch = 2
                    
                    elif switch == 2:
                        user['send_sensor']('x2', str(x))
                        user['send_sensor']('y2', str(y))
                        user['send_broadcast']('pixel_update2')
                        switch = 0
    
    def scratch_auth(self, username, password, uid):
        details = {'username' : username, 'password' : password}
        string = "http://scratch.mit.edu/api/authenticateuser?"
        string = string + urllib.urlencode(details)
        fp = urllib.urlopen(string)
        result = fp.read()
        fp.close()
        result = result.decode("utf8")
        if result == ' \r\nfalse':
            return 0
        
        else:
            result = result.split(':')
            if result[2] == 'blocked' or result[2] in self.banned:
                return 0
            
            else:
                self.placers.append(uid)
    
    def reset_map(self):
        self.art = {'0' : {'0' : 1}}
        for user_id in self.users:
            self.update_whole(user_id)
