# Chat.PY v4 for LSTC-Green
# Two options, Character Chat, or regular.
# Character Chat: You play an avatar that can move around and when
# you chat, it appears as a "talk bubble" above the character.
#
# Regular: Just an IRC like client. :)
# By: Magnie

import threading

class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {}
        
        self.ranks = []
        
        self.channel_data = {} 
        self.channel_cache = {} # channel : [users]
        
        self.account_data = {}
    
    def run(self):
        pass
    
    def new_user(self, user_id, functions):
        self.users[user_id] = Client(functions)
    
    def lost_user(self, user_id):
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        pass
    
    def disconnect(self):
        pass
    
    # Message functions
    
    def message_server(self, message):
        for user_id in self.users:
            user = self.users[user_id]
            user.send_sensor('from', 'ServerNinja')
            user.send_sensor('message', message)
            user.send_broadcast('new_message')
    
    def message_channel(self, channel, message):
        if channel not in self.channel_cache:
            return
        
        for user_id in self.channel_cache[channel]:
            user = self.users[user_id]
            user.send_sensor('from', channel)
            user.send_sensor('message', message)
            user.send_broadcast('new_message')
    
    def message_user(self, from_user, user, message):
        for user_id in self.users:
            user = self.users[user_id]
            if user.name == user:
                user.send_sensor('from', from_user)
                user.send_sensor('message', message)
                user.send_broadcast('new_message')
                break

class Client(object):
    
    def __init__(self, functions):
        self.functions = functions
        self.send_broadcast = functions['broadcast']
        self.send_sensor = functions['sensor-update']
        
        self.name = 'User' + functions['user-id']
        self.channel_ranks = {} # channel : rank
        self.server_rank = 0
        
        self.logged_in = False
        
        # Character Positions
        self.x_pos = 0
        self.y_pos = 0
    
    def new_message(self, raw_message):
        message = raw_message.split(' ')
        cmd = message[0]
        args = message[1:]
        
        # Basic chat
        if cmd == 'send':
            pass
        
        elif cmd == 'pm':
            pass
        
        elif cmd == 'join':
            pass
        
        elif cmd == 'part':
            pass
        
        elif cmd == 'nick':
            pass
        
        # Authentication
        elif cmd == 'login':
            pass
        
        elif cmd == 'logout':
            pass
        
        elif cmd == 'whois':
            pass
        
        # Channel moderation
        elif cmd == 'kick':
            pass
        
        elif cmd == 'ban':
            pass
        
        elif cmd == 'promote':
            pass
        
        elif cmd == 'demote':
            pass
        
        elif cmd == 'list':
            pass
        
        # Server moderation
        elif cmd == 'server':
            sub = args[0]
            args = args[1:]
            
            if sub == 'kick':
                pass
            
            elif sub == 'ban':
                pass
            
            elif sub == 'promote':
                pass
            
            elif sub == 'demote':
                pass
            
            elif sub == 'forcekill':
                pass
            
            elif sub == 'nick':
                pass
            
            elif sub == 'name_change':
                
                if args[0] == 'enable':
                    pass
                
                elif args[0] == 'disable':
                    pass
    
    # Command functions
    # Basic chat commands.
    
    def cmd_send(self, channel, message):
        # Send a message to a channel
        pass
    
    def cmd_pm(self, user, message):
        # Send a message to another user
        pass
    
    def cmd_join(self, channel):
        # Join a new channel
        pass
    
    def cmd_part(self, channel):
        # Leave a channel
        pass
    
    def cmd_nick(self, new_name):
        # Change the name.
        pass
    
    # Authentication commands
    
    def cmd_login(self, scratch_user, scratch_password):
        # Authenticate with a Scratch account
        pass
    
    def cmd_logout(self):
        # Deauthenticate
        pass
    
    def cmd_whois(self, user):
        pass
    
    # Channel moderation commands
    
    def cmd_kick(self, channel, user):
        # Force a user to leave a channel.
        pass
    
    def cmd_ban(self, channel, user):
        # Keep a user from entering this channel.
        pass
    
    def cmd_promote(self, channel, user, mod):
        # Increase a user's rank.
        pass
    
    def cmd_demote(self, channel, user, mod):
        # Decrease a user's rank.
        pass
    
    # Server moderation commands
    
    def cmd_server_kick(self, user):
        # Force a user to leave the server/plugin.
        pass
    
    def cmd_server_ban(self, user):
        # Ban a user from using this server/plugin.
        pass
    
    def cmd_forcekill(self, user):
        # Force a user to disconnect from the server in whole.
        pass
    
    def cmd_server_promote(self, user, mod):
        # Increase a user's rank on the server.
        pass
    
    def cmd_server_demote(self, user, mod):
        # Decrease a user's rank on the server.
        pass
    
    def cmd_server_nick(self, user, new_name):
        # Force a user to change names.
        pass
    
    def cmd_disable_name(self, user):
        # Disable name changing for a user.
        pass
    
    def cmd_enable_name(self, user):
        # Enable name changing for a user.
        pass
    
    # Info commands
    
    def cmd_list(self, channel):
        # List who is in the channel.
        pass
    
