#!/usr/bin/env python
# Little Server That Can v2.x Green Version
# By: Magnie

import hashlib
from array import array
import time

import gevent
from gevent.server import StreamServer

from gevent import monkey
monkey.patch_socket()

DEBUG_MODE = True


class Server(object):
    
    def __init__(self, load_plugins, port=42001, host='0.0.0.0'):
        #Greenlet.__init__(self)
        self.stream = StreamServer((host, port), self.handler)
        self.recv_size = 1024
        
        # RSC Parser
        self.parser = ScratchParser()
        
        # Store the threads here.
        self.threads = []
        
        # Whitelist/Blacklist
        self.whitelist = []
        self.blacklist = []
        
        # Store plugin objects here.
        self.plugins = {}
        self.plugin_bans = {}
        
        # Load each plugin
        for plugin in load_plugins:
            try:
                # Load the plugin file and call the server class.
                exec("""
import plugins.{0}
self.plugins[plugin] = plugins.{0}.Server()
""").format(plugin)

                # Start the plugin thread.
                self.plugins[plugin].start()
            
                # Create a plugin user ban list
                self.plugin_bans[plugin] = set([])
            
            except Exception, e:
                print '{0} broke and gave error: {1}'.format(plugin, e)
            
    
    def _run(self):
        """When the Server is started"""
        
        # The starting id number.
        self.user_id = 0
        
        # Start accepting connections
        try:
            self.stream.serve_forever()
        
        # Wait until kill signal is sent.
        except KeyboardInterrupt:
            pass
        
        # Shut down plugins.
        for plugin in self.plugins:
            plugin = self.plugins[plugin]
            plugin.disconnect()
            plugin.running = False
            plugin.join()
    
    def handler(self, socket, address): # Might use this for blacklists.
        """The handle for new connections"""
        self.threads.append(Client(socket, address, self))
    
    def reload_plugin(self, name):
        """Restart a plugin to run the most recent version. Useful for updating
        plugins without restarting the server."""
        if name in self.plugins:
            # Shut down the plugin
            self.plugins[name].disconnect()
            debug(self.threads)
            for client in self.threads:
                if name in client.plugins:
                    client.plugins.remove(name)
                
                debug(client.plugins)
            
            # import the new version and start up that server.
            try:
                tmp_plugin = getattr(__import__('plugins.' + name), name)
                reload(tmp_plugin)
            except NameError:
                exec('import plugins.' + name + ' as ' + tmp_plugin)
            
            self.plugins[name] = tmp_plugin.Server()
            self.plugins[name].start()
            
            
        

class Client(object):
    
    def __init__(self, socket, address, server):
        
        self.socket = socket
        self.addr = address
        
        # This is a complete and total hack, for some reason
        # Server.handler() won't append it like it's supposed to.
        server.threads.append(self)
        debug(server.threads)
        
        # Create a "public hash" of the IP. Might need to add a salt.
        self.ip_hash = hashlib.md5(self.addr[0]).hexdigest()
        
        self.keep_alive = True
        print s.blacklist
        if self.addr[0] in s.blacklist or self.ip_hash in s.blacklist:
            print self.ip_hash + ' is banned.'
            self.socket.close()
            return
        
        # Stores the plugins in use.
        self.plugins = set([])
        
        # Used in the plugins to separate the clients.
        self.user_id = str(s.user_id)
        
        # Increment to keep from clashing.
        s.user_id += 1
        
        # Can be used by plugins to force clients to update.
        self.client_version = 0;
        
        print self.ip_hash + ' has connected.'
        
        # Start the main part of the client.
        self._run()
    
    def _run(self):
        """When the Client is started.
        Waits for messages from clients."""
        self.running = True
        
        while self.running:
            # Receive Data
            try:
                data = self.socket.recv(s.recv_size)
            except:
                # If an error occurs, pretend no data was sent.
                data = None
            
            # If no data is available, stop the loop.
            if not data or data == '\x00\x00\x00\x00':
                self.running = False
                break
            
            # Divide the messages if there are more than one.
            messages = s.parser.get_messages(data)
            for message in messages:
                # Parse message
                sent = s.parser.parse(message)
                
                for i in sent:
                    # Send to another function.
                    self.deal_with(i)
            
            if not self.keep_alive:
                self.running = False
                break
        
        # Close the connection.
        for plugin in list(self.plugins):
            try:
                self.leave_plugin(plugin)
            
            except Exception, e:
                print e
        
        print self.ip_hash + ' has disconnected.'
        self.socket.close()
    
    def deal_with(self, raw_message):
        """
        Parses a raw message from Scratch and puts it into a usable format.
        """
        # Format: :[command] [plugin] [message]
        # Example: :> template reset
        # Check if it's server specific data
        if raw_message[0] != ':':
            return
        
        # Split the message into parsable data.
        message = raw_message.split(' ')
        request = message[0][1:]
        args = message[1:]
        
        # Use a plugin.
        if request == '+':
            if args[0] not in self.plugins:
                self.plugins.add(args[0])
                
                # Tell plugin that this user has connected.
                plugin = s.plugins[args[0]]
                plugin.new_user(self.user_id, self.functions())
        
        # Remove a plugin.
        elif request == '-':
            if args[0] in self.plugins:
                self.plugins.remove(args[0])
                
                # Tell plugin that this user has disconnected.
                plugin = s.plugins[args[0]]
                plugin.lost_user(self.user_id)
        
        # Server plugin reload.
        elif request == '*' and args[0] == '1234': # TODO: Add password.
            s.reload_plugin(args[1])
        
        # Can be used for latency.
        elif request == 'ping':
            self.send_broadcast(':pong')
        
        # Update client version number
        elif request == 'version':
            if isinstance(args[0], float) or isinstance(args[0], int):
                self.client_version = args[0]
        
        # Return the minutes since 2000.
        elif request == 'time':
            self.send_sensor('stime', str(round(time.time() / 60)))
        
        # Forward to plugin.
        elif request == '>':
            if args[0] in self.plugins:
                # Put the full message together
                forward = ' '.join(args[1:])
                
                # Forward it to the plugin.
                plugin = s.plugins[args[0]]
                try:
                    gevent.spawn(plugin.new_message,
                                 self.user_id,
                                 forward)
                
                except Exception:
                    pass
    
    def functions(self):
        """Returns a dictionary of functions that can be used by plugins."""
        # Allow plugins to send broadcasts, messages, and implement
        # a ban list.
        return {'broadcast' : self.send_broadcast,
                'sensor-update' : self.send_sensor,
                'ip-hash' : self.ip_hash,
                'user-id' : self.user_id,
                'version' : self.client_version,
                'leave-plugin' : self.leave_plugin,
                'force-kill' : self.force_kill,
                'server-ban' : self.server_ban,
                'server-unban' : self.server_unban}
    
    def force_kill(self):
        # Force a user to disconnect.
        self.keep_alive = False;
    
    def server_ban(self, ip_hash):
        # Ban this IP hash.
        s.blacklist.append(ip_hash) # FIX: Needs to use server, not 's'.
    
    def server_unban(self, ip_hash):
        # Remove than ban on this IP hash.
        
        if ip_hash in s.blacklist:
            s.blacklist.remove(ip_hash) # FIX: Needs to use server, not 's'.
    
    def leave_plugin(self, plugin):
        """Stop the client from using this plugin anymore."""
        if plugin in self.plugins:
            self.plugins.remove(plugin)
            
            # Tell plugin that this user has disconnected.
            plugin = s.plugins[plugin]
            plugin.lost_user(self.user_id)
    
    def send_broadcast(self, message):
        """Sends a broadcast to Scratch."""
        message = 'broadcast "{0}"'.format(message)
        # Add the length to the beginning of the message.
        message = s.parser.add_length(message)
        # Send it to the client.
        try:
            self.socket.send(message)
        
        except: # TODO: Disconnect user if message fails.
            self.socket.close()
    
    def send_sensor(self, name, value):
        """Sends a sensor-update to Scratch."""
        message = 'sensor-update "{0}" "{1}"'.format(name, value)
        # Add the length to the beginning of the message.
        message = s.parser.add_length(message)
        # Send it to the client.
        try:
            self.socket.send(message)
        
        except: # TODO: Disconnect user if message fails.
            self.socket.close()
    
def dict_from_flat_generator(gen):
    """Convert [key, value, key, value] iterable to dict"""
    return dict(zip(*[gen]*2))
    # see http://countergram.com/python-group-iterator-list-function

class ScratchParser(object):
    # Thanks to blob8108:
    # http://scratch.mit.edu/forums/viewtopic.php?pid=1424108#p1424108
    MSG_TYPES = ["broadcast", "sensor-update", "peer-name"]
    
    def get_messages(self, message):
        i = 0
        while i < len(message):
            # Read the first four characters.
            temp = message[i:i + 4]
            length = temp[-1] + temp[-2] + temp[-3] + temp[-4]
            # Convert from binary number to integer
            length = array("I", length)[0]
            # Add the message to messages.
            yield message[i + 4:i + length + 4]
            # Change i to next chunk.
            i += length + 4
    
    def parse(self, msg):
        """Parse Scratch mesh message using the appropriate helper function.
        
        Raises SyntaxError for unquoted strings.
        """
        def parse_parts(data):
            chars = iter(data)
            part = None
            while 1:
                try:
                    char = chars.next()
                except StopIteration: # End of message!
                    break
                
                # Double-quoted Strings
                if char == '"':
                    lookahead = None
                    
                    if part:
                        parts.append(part)
                    # quoted string
                    part = ""
                    while 1:
                        try:
                            char = chars.next()
                        except StopIteration:
                            import pdb; pdb.set_trace()
                            print 'Unclosed string (")'
                            return
                        
                        if char == '"':
                            # double-quotes are escaped as double double-quotes
                            try:
                                lookahead = chars.next()
                            except StopIteration: # End of message!
                                yield part
                                return
                            
                            if lookahead == '"':
                                part += '"'      # escaped double-quote
                                lookahead = None # reset lookahead
                            else:
                                yield part  
                                break       # stop building string
                            
                        else:
                            part += char
                    part = None
                    
                    if lookahead is None:
                        continue
                    else:
                        char = lookahead # Pass char to unquoted, below
                                         # vv
                
                # Space separates values
                if char == ' ': 
                    if part is not None:
                        yield part
                        part = None
                
                # Unquoted strings
                else:
                    if part is None: part = ""
                    part += char
            
            if part is not None:
                yield part
        
        
        for type in self.MSG_TYPES:
            if msg.startswith(type):
                data = msg[len(type):]
                parts = parse_parts(data)
                func = getattr(self, "parse_"+type.replace("-", "_"))
                return func(parts)
        
        raise(NotImplementedError("Unknown message type: %r" % msg))
    
    
    def parse_broadcast(self, parts):
        return list(parts)
        # do stuff...
        
    def parse_sensor_update(self, parts):
        return dict_from_flat_generator(parts) 
        # do stuff...
    
    def parse_peer_name(self, parts):
        return list(parts)[0]
        # do stuff...
    
    def add_length(self, cmd):
        # Defines the length of each message.
        n = len(cmd)
        a = array('c')
        a.append(chr((n >> 24) & 0xFF))
        a.append(chr((n >> 16) & 0xFF))
        a.append(chr((n >>  8) & 0xFF))
        a.append(chr(n & 0xFF))
        return (a.tostring() + cmd)

def debug(string):
    if DEBUG_MODE:
        print string

if __name__ == "__main__":
    s = Server(['template', 'chat4']) 
    s._run()
