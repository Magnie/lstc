#!/usr/bin/env python
# Little Server That Can v2.x
# By: Magnie

import socket
import threading
import traceback
import random
import hashlib

from array import array


class Server(object):
    
    def __init__(self, host="0.0.0.0", # 0.0.0.0 means anyone can connect
                       port=42001,
                       backlog=5):
        self.sock = socket.socket(socket.AF_INET,
                                  socket.SOCK_STREAM)
        
        self.sock.bind((host, port))
        self.sock.listen(backlog)
        
        self.key = ''
        for x in xrange(0, 4):
            self.key += str(random.randrange(0, 9))
        
        log(self.key, fn='server_key')
        
        # Type in the filenames (exclude the extentions) for each
        # plugin you want.
        self.load_plugins = ['bit_art', 'chat3']
        
        # Currently does nothing, but in the future, you should be
        # able to limit how many users can be on the server.
        self.max_clients = 50
        
        self.plugins = {}
        
        for plugin in self.load_plugins:
            try:
                exec('''from plugins import {0}
p = {0}.Server()
p.start()'''.format(plugin))
                self.plugins[plugin] = p
            
            except:
                log(traceback.format_exc())
            
        
        self.mode = 'BLACKLIST' # BLACKLIST means "allow everybody
                                # but: [IPs here]", WHITELIST means "allow
                                # nobody but: [IPs here]".
        
        if self.mode == 'WHITELIST':
            try: # Load whitelist, create one if it doesn't exist.
                t_file = open('whitelist.txt', 'r').read()
                self.whitelist = t_file.split('\n')
        
            except IOError, e:
                log(e)
                open('whitelist.txt', 'w').close()
                self.whitelist = []
            
        else:
            try: # Load blacklist, create one if it doesn't exist.
                t_file = open('blacklist.txt', 'r').read()
                self.blacklist = t_file.split('\n')
        
            except IOError, e:
                log(e)
                open('blacklist.txt', 'w').close()
                self.blacklist = []
    
    def run(self):
        self.running = 1
        self.threads = []
        
        id_count = 0
        try:
            while self.running:
                # Increase so no client has the same ID.
                id_count += 1
                
                # Waits for a client then accepts it.
                c = Client(self.sock.accept(), id_count)
                
                # Create a hash of the IP to hide from admins/mods.
                m = hashlib.md5()
                m.update(c.address[0])
                c.ip_hash = m.hexdigest()
                
                if self.mode == 'BLACKLIST':
                    if c.ip_hash not in self.blacklist:
                        c.start() # Starts it.
                
                        # Adds it to a list so the variable c and be used
                        # for the next client.
                        self.threads.append(c)
                        log(str(c.ip_hash) + ' has connected.')
                    
                    else:
                        log(str(c.ip_hash) + ' attempted to connected.')
                        c.close()
                else:
                    if c.ip_hash in self.whitelist:
                        c.start() # Starts it.
                
                        # Adds it to a list so the variable c and be used
                        # for the next client.
                        self.threads.append(c)
                        log(str(c.ip_hash) + ' has connected.')
                    
                    else:
                        log(str(c.ip_hash) + ' attempted to connected.')
                        c.close()
                        c.client.close()
                
                '''
                i = 0
                to_delete = []
                for thread in self.threads:
                    if thread.remove_self:
                        to_delete.append(i)
                    
                    i += 1
                
                for i in to_delete:
                    self.threads.pop(i)
                '''
            
        except KeyboardInterrupt:
            pass
        
        print 'Shutting down plugins.'
        
        for p in self.plugins:
            plugin_server = self.plugins[p]
            plugin_server.disconnect()
            plugin_server.join()
        
        del self.plugins
        
        print 'Shutting down clients.'
        
        # Disconnect all clients.
        for c in self.threads: # For each thread
            c.client.close()
            c.running = 0
            c.join() # End that thread.
        
        del self.threads
            
        print 'Closing socket.'
        
        self.sock.close() # Disconnect socket.
    
    def reload_plugin(self, plugin):
        if plugin in self.plugins:
            try:
                self.plugins[plugin].disconnect()
            
            except:
                log(traceback.format_exc())
            
            del self.plugins[plugin]
        
        try:
            tmp_plugin = getattr(__import__('plugins.' + plugin),
                                            plugin)
            reload(tmp_plugin)
        except NameError:
            exec('import plugins.' + plugin + ' as ' + tmp_plugin)
        
        try:
            self.plugins[plugin] = tmp_plugin.Server()
            self.plugins[plugin].start()
        
            for user in self.threads:
                self.plugins[plugin].new_user(user.user_id,
                                              user.functions())
        
        except:
            log(traceback.format_exc())


class Client(threading.Thread):
    
    def __init__(self, (client, address), user_id):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 1024
        
        self.plugins = []
        self.user_id = user_id
        
        self.key = ''
        
        self.remove_self = False
    
    def run(self):
        self.running = 1
        
        while self.running:
            try:
                data = self.client.recv(self.size)
                data = self.parse_data(data)
                
            except:
                log(traceback.format_exc())
                data = None
            
            if data == None:
                self.running = 0
                break
            
            for broadcast in data['broadcast']:
                self.new_broadcast(broadcast)
        
            for sensor in data['sensor-update']:
                value = data['sensor-update'][sensor]
                self.new_sensor(sensor, value)
        
        
        self.close()
        self.client.close()
    
    def new_broadcast(self, message):
        if message[0] == ':':
            # Colon means send message to loaded plugins.
            self.forward_msg(message[1:])
        
        elif message[0] == '<':
            # Greater-than sign means load a plugin.
            
            # Check if it exists.
            if message[1:] in s.plugins:
                
                # Check if it's already loaded. Remove if it is.
                if message[1:] in self.plugins:
                    try:
                        s.plugins[message[1:]].lost_user(self.user_id)
            
                    except:
                        log(traceback.format_exc())
                    
                    self.plugins.remove(message[1:])
                
                try:
                    # Then load it [again].
                    plugin = message[1:]
                    self.plugins.append(plugin)
                    s.plugins[plugin].new_user(self.user_id,
                                               self.functions())
                
                except:
                    log(traceback.format_exc())
        
        elif message[0] == '*':
            if self.key == s.key:
                try:
                    s.reload_plugin(message[1:])
                
                except:
                    log(traceback.format_exc())
            
            else:
                self.key = message[1:]
        
    def new_sensor(self, name, value):
        if name == ':server':
            self.forward_msg(value)
    
    def forward_msg(self, message):
        for plugin in self.plugins:
            try:
                s.plugins[plugin].new_message(self.user_id,
                                              message)
            
            except:
                log(traceback.format_exc())
    
    def parse_data(self, message):
        if not message:
            return None
        
        sensors = {}
        broadcasts = []

        commands = []
        i = 0
        while True: # Separate the messages if there is more than one.
            length = message[i:i + 4]
            length = array("I", length)[0]
            command = message[i + 4:i + length + 4]
            commands.append(command)
            if (i + length + 4) < len(message):
                i = (i+4) + length
            else:
                del command
                break
        
        for command in commands: # Parse each section.
            # broadcast "broadcast message here"
            if command[0] == 'b':
                command = command.split('"')
                command.pop(0)
                command = '"'.join(command[0:])
                broadcasts.append(command[:-1])
            
            # sensor-update "name" "string"
            # sensor-update "name" 023456789
            elif command[0] == 's':
                command = command.split('sensor-update "', 1)
                command = command[1]
                command = command.split('" ', 1)
                
                if command[1][0] == '"':
                    command[1] = command[1][1:-2]
                
                sensors[command[0]] = command[1]
    
        return dict([('sensor-update', sensors), # Organize it.
                     ('broadcast', broadcasts)])
    
    def add_length(self, cmd):
        # Defines the length of each message.
        n = len(cmd)
        a = array('c')
        a.append(chr((n >> 24) & 0xFF))
        a.append(chr((n >> 16) & 0xFF))
        a.append(chr((n >>  8) & 0xFF))
        a.append(chr(n & 0xFF))
        return (a.tostring() + cmd)
    
    # Plugin accessible functions.
    
    def functions(self):
        return {'send_broadcast' : self.send_broadcast,
                'send_sensor' : self.send_sensor,
                'ban_user' : self.ban_user,
                'unban_user' : self.unban_user,
                'force_leave' : self.force_disconnect,
                'ip' : self.ip_hash,
                'id' : self.user_id}
    
    def ban_user(self, ip):
        s.blacklist.append(ip)
        
        for user in s.threads:
            if user.ip_hash == ip:
                user.close()
                user.client.close()
    
    def unban_user(self, ip):
        s.blacklist.remove(ip)
    
    def force_disconnect(self):
        self.close()
        self.client.close()
    
    def send_sensor(self, name, value):
        message = 'sensor-update "{0}" "{1}"'.format(name, value)
        message = self.add_length(message)
        try:
            self.client.send(message)
        
        except:
            self.close()
            self.client.close()
            log(self.ip_hash + ' died late.')
    
    def send_broadcast(self, name):
        message = 'broadcast "{0}"'.format(name)
        message = self.add_length(message)
        try:
            self.client.send(message)
        
        except:
            self.close()
            self.client.close()
            log(self.ip_hash + ' died late.')
    
    
    # Closing functions
    
    def close(self):
        for plugin in self.plugins:
            s.plugins[plugin].lost_user(self.user_id)
        
        del self.plugins
        self.remove_self = True

def log(string, fn='server'):
    string = str(string)
    print string
    try:
        log_file = open(fn + ".log", 'a')
        log_file.write('\n' + string)
        log_file.close()
    except IOError, e:
        log_file = open(fn + ".log", 'w')
        log_file.write(string)
        log_file.close()

if __name__ == "__main__": 
    s = Server() 
    s.run()
