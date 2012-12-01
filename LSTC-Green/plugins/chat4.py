# Chat.PY Plugin

import threading

class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {}
        
        self.channel_data = {}
        
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

class Client(object):
    
    def __init__(self, functions):
        self.functions = functions
        
        self.name = 'User' + functions['user-id']
        self.channel_ranks = {} # channel : rank
        self.server_rank = '-'
        
        self.logged_in = False
    
    def new_message(self, message):
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
        pass
    
    def cmd_enable_name(self, user):
        pass
