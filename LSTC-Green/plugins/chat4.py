# Chat.PY v4 for LSTC-Green
# Two options, Character Chat, or regular.
# Character Chat: You play an avatar that can move around and when
# you chat, it appears as a "talk bubble" above the character.
#
# Regular: Just an IRC like client. :)
# By: Magnie

# Ranking System:
# Owner - 0
# Admin - 1
# Operator - 2
# Half-Op - 3
# Voice - 4
# Normal - 5
# Shunned - 6

import threading

from time import strftime

class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {}
        
        self.ranks = ['Owner', 'Admin', 'Operator', 'Half-Op',
                      'Voice', 'Normal', 'Shunned']
        
        self.channel_data = {'scratch' : {'ranked' : {'Magnie' : 0},
                                          'whitelist' : ['Magnie'],
                                          'blacklist' : [],
                                          'mutelist': [],
                                          'flags' : 'bp',
                                          'motd' : 'Welcome!'}} 
        self.channel_cache = {} # channel : [users]
        for channel in self.channel_data:
            self.channel_cache[channel] = []
        
        self.account_data = {}
        
        self.banned_accounts = set([])
    
    def run(self):
        pass
    
    def new_user(self, user_id, functions):
        self.users[user_id] = Client(functions, self)
    
    def lost_user(self, user_id):
        user = self.users[user_id]
        channels = user.channel_ranks
        for channel in channels:
            user.cmd_part(channel)
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        self.users[user_id].new_message(message)
    
    def disconnect(self):
        pass
    
    # Functions
    
    def get_id(self, name):
        for user_id in self.users:
            if self.users[user_id].name == name:
                return user_id
    
    # Message functions
    
    def message_server(self, message):
        # Send message to every user on the server.
        for user_id in self.users:
            user = self.users[user_id]
            self.message_send('ServerNinja', user, message)
    
    def message_channel(self, channel, message):
        # Send message to only people in a specific channel.
        if channel not in self.channel_cache:
            return
        
        for user_id in self.channel_cache[channel]:
            user = self.users[user_id]
            self.message_send(channel, user, message)
    
    def message_user(self, from_user, user_name, message):
        # Send message to a specific person.
        for user_id in self.users:
            user = self.users[user_id]
            if user.name == user_name:
                self.message_send(from_user, user, message)
                break
    
    def message_send(self, from_user, to_user, message):
        # Send the message and other associated data.
        # Set to current time.
        current_time = strftime('%H:%M:%S')
        # Add timestamp
        message = '[{0}]{1}'.format(current_time, message)
        # Update from sensor.
        to_user.send_sensor('from', from_user)
        # Update message sensor.
        to_user.send_sensor('message', message)
        # Tell client that there is a new message.
        to_user.send_broadcast('new_message')

class Client(object):
    
    def __init__(self, functions, server):
        self.functions = functions
        self.send_broadcast = functions['broadcast']
        self.send_sensor = functions['sensor-update']
        
        self.name = 'User' + functions['user-id']
        self.channel_ranks = {} # channel : rank
        self.server_rank = 0
        
        self.logged_in = False
        self.logged_in_name = None
        
        self.channel = 'none'
        
        self.name_change = True
        self.char_chat = False
        
        # Character Positions
        self.x_pos = 0
        self.x_vel = 0
        
        self.y_pos = 0
        self.y_vel = 0
        
        # Access to server class functions
        self.server = server
        
        message = "Welcome to Chat.PY 4.0! If you are seeing this\
then you are connected to the server!"
        self.send_sensor('message', message)
        self.send_broadcast('new_message')
    
    def new_message(self, raw_message):
        message = raw_message.split(':', 1)
        cmd = message[0]
        args = None
        if len(message) == 2:
            args = message[1]
        
        # Basic chat
        if cmd == 'send':
            self.channel, chat_message = args.split(':', 1)
            if chat_message[0] != '/':
                self.cmd_send(self.channel, chat_message)
            
            else:
                message_split = chat_message.split(' ', 1)
                cmd = message_split[0][1:]
        
                if len(message_split) == 2:
                    args = message_split[1]
                
                else:
                    args = None
        
        print cmd, args
        
        if cmd == 'pm':
            args = args.split(' ', 1)
            self.cmd_pm(args[0], args[1])
        
        elif cmd == 'join':
            self.cmd_join(args)
        
        elif cmd == 'part':
            if args:
                self.cmd_part(args)
            
            else:
                self.cmd_part(self.channel)
        
        elif cmd == 'nick':
            self.cmd_nick(args)
        
        # Authentication
        elif cmd == 'login':
            args = args.split(' ', 1)
            self.cmd_login(args[0], args[1])
        
        elif cmd == 'logout':
            self.cmd_logout()
        
        elif cmd == 'whois':
            self.cmd_whois(args)
        
        # Channel moderation
        elif cmd == 'kick':
            args = args.split(' ', 1)
            if len(args) == 2: # /kick [channel] [user]
                self.cmd_kick(args[0], args[1])
            
            else: # /kick [user]
                self.cmd_kick(self.channel, args[0])
        
        elif cmd == 'ban':
            args = args.split(' ', 1)
            if len(args) == 2:
                # args = [channel, username]
                self.cmd_ban(args[0], args[1])
            
            else:
                self.cmd_ban(self.channel, args[0])
        
        elif cmd == 'unban':
            args = args.split(' ', 1)
            if len(args) == 2:
                # args = [channel, username]
                self.cmd_unban(args[0], args[1])
            
            else:
                self.cmd_unban(self.channel, args[0])
        
        elif cmd == 'promote':
            args = args.split(' ', 2)
            if len(args) == 3:
                # args = [channel, username, mod]
                self.cmd_promote(args[0], args[1])
            
            else:
                self.cmd_promote(self.channel, args[0])
        
        elif cmd == 'demote':
            args = args.split(' ', 2)
            if len(args) == 3:
                # args = [channel, username, mod]
                self.cmd_demote(args[0], args[1])
            
            else:
                self.cmd_demote(self.channel, args[0])
        
        elif cmd == 'list':
            if args:
                # args = channel
                self.cmd_list(args)
            
            else:
                self.cmd_list(self.channel)
        
        elif cmd == 'help':
            self.cmd_help()
        
        # Use character chat?
        elif cmd == 'character':
            if args == 'True':
                self.char_chat = True
            
            else:
                self.char_chat = False
        
        # Server moderation
        elif cmd == 'server':
            sub = args[0]
            args = args[1:]
            
            if sub == 'kick':
                args = args.split(' ', 1)
                if len(args) == 2:
                    self.cmd_server_kick(args[0], args[1])
                
                else:
                    self.cmd_server_kick(self.channel, args[0])
            
            elif sub == 'ban':
                args = args.split(' ', 1)
                if len(args) == 2:
                    self.cmd_server_ban(args[0], args[1])
                
                else:
                    self.cmd_server_ban(self.channel, args[0])
            
            elif sub == 'unban':
                args = args.split(' ', 1)
                if len(args) == 2:
                    self.cmd_server_unban(args[0], args[1])
                
                else:
                    self.cmd_server_unban(self.channel, args[0])
            
            elif sub == 'promote':
                args = args.split(' ', 2)
                if len(args) == 3:
                    self.cmd_server_promote(args[0], args[1])
                
                else:
                    self.cmd_server_promote(self.channel, args[0])
            
            elif sub == 'demote':
                args = args.split(' ', 2)
                if len(args) == 3:
                    self.cmd_server_demote(args[0], args[1])
                
                else:
                    self.cmd_server_demote(self.channel, args[0])
            
            elif sub == 'forcekill':
                self.cmd_server_forcekill(args)
            
            elif sub == 'nick':
                args = args.split(' ', 1)
                self.cmd_server_nick(args[0], args[1])
            
            elif sub == 'name_change':
                args = args.split(' ', 1)
                if args[0] == 'enable':
                    self.cmd_enable_name(args[1])
                
                elif args[0] == 'disable':
                    self.cmd_disable_name(args[1])
    
    # Control Ranked Commands
    def test_srank(self, rank):
        if not self.logged_in:
            return False
            
        if self.server_rank <= rank:
            return True
        
        return False
    
    def test_crank(self, channel, rank):
        if not self.logged_in:
            return False
        
        if self.channel_ranks[channel] <= rank:
            return True
        
        return False
    
    # Command functions
    # Basic chat commands.
    
    def cmd_send(self, channel, message):
        # Send a message to a channel
        if channel not in self.channel_ranks:
            self.response_error('not in channel')
            return
        
        if self.channel_ranks[channel] == 'mute':
            self.response_error('muted')
            return
            
        full_message = '{0}: {1}'.format(self.name, message)
        full_message = self.censor(full_message)
        
        self.server.message_channel(channel, full_message)
    
    def cmd_pm(self, user, message):
        # Send a message to another user
        
        if not self.test_srank(4): return
        
        self.server.message_user(self.name, user, message)
    
    def cmd_join(self, channel):
        # Join a new channel
        
        # If the channel doesn't exist, create it.
        if channel not in self.server.channel_data:
            channel_data = {'ranked' : {self.name : 2},
                            'whitelist' : [self.name],
                            'blacklist' : [],
                            'mutelist': [],
                            'flags' : 'b',
                            'motd' : 'Welcome!'}
            
            self.server.channel_data[channel] = channel_data
            self.server.channel_cache[channel] = []
        
        channel_data = self.server.channel_data[channel]
        # Check if the whitelist applies.
        if 'w' in channel_data['flags']:
            if self.logged_in_name not in channel_data['whitelist']:
                self.response_error(message_type='whitelist')
                return
        
        # Check if the blacklist applies.
        if 'b' in channel_data['flags']:
            if self.name in channel_data['blacklist']:
                self.response_error(message_type='blacklist')
                return
        
        if self.logged_in_name in channel_data['ranked']:
            name = channel_data['ranked'][self.logged_in_name]
            self.channel_ranks[channel] = name
        
        else:
            self.channel_ranks[channel] = 5
        
        user_id = self.functions['user-id']
        self.server.channel_cache[channel].append(user_id)
        
        self.send_sensor('channel', channel)
        self.send_broadcast('joined')
        self.response_common(channel, 'join', self.name, channel)
    
    def cmd_part(self, channel):
        # Leave a channel
        del self.channel_ranks[channel]
        user_id = self.functions['user-id']
        self.server.channel_cache[channel].remove(user_id)
        
        self.response_common(channel, 'part', self.name, channel)
        
        # If it's not a permanent channel, delete after the last
        # user leaves.
        channel_data = self.server.channel_data[channel]
        if len(self.server.channel_cache[channel]) == 0:
            if 'p' not in channel_data['flags']:
                del self.server.channel_data[channel]
        
        self.send_sensor('channel', channel)
        self.send_broadcast('parted')
    
    def cmd_nick(self, new_name):
        # Change the name.
        
        # Check if they are allowed to change their name.
        if not self.name_change:
            self.response_error(message_type='name disabled')
            return
        
        for channel in self.channel_ranks:
            self.response_common(channel, 'rename',
                                 self.name, new_name)
        
        self.name = new_name
    
    # Authentication commands
    
    def cmd_login(self, scratch_user, scratch_password):
        # Authenticate with a Scratch account
        # Make sure the user isn't already logged in.
        if self.test_srank(4):
            self.response_error(message_type='logged in')
            return
        
        details = {'username' : scratch_user,
                   'password' : scratch_password}
        string = "http://scratch.mit.edu/api/authenticateuser?"
        string = string + urllib.urlencode(details)
        fp = urllib.urlopen(string)
        result = fp.read()
        fp.close()
        result = result.decode("utf8")
        
        banned = self.server.banned_accounts
        
        if result == ' \r\nfalse':
            # Login failed.
            self.response_error(message_type='login failed')
            return
        
        else:
            result = result.split(':')
            if result[2] == 'blocked' or result[2] in banned:
                # Banned by the Scratch Team or banned just for this.
                self.response_error(message_type='login failed')
                return
            
            else:
                # Successfully logged in.
                self.logged_in = True
                self.logged_in_name = scratch_user
                
                accounts = self.server.account_data
                if scratch_user in accounts:
                    # If the account exists, use the saved rank.
                    self.server_rank = accounts[scratch_user]
                
                else:
                    # If the account doesn't exist, create it.
                    accounts[scratch_user] = 4
                    self.server_rank = 4
    
    def cmd_logout(self):
        # Deauthenticate
        self.logged_in = False
        self.logged_in_name = None
        self.server_rank = 5
    
    def cmd_whois(self, user):
        for client in self.server.users:
            client = self.server.users[client]
            if client.name == user:
                message = 'Whois on {0}: \n'
                message += 'Logged in: {1} \n'
                if client.logged_in:
                    message += 'Logged in as: {2}'
                    message += 'Server rank: {3}'
                    message = message.format(user, client.logged_in,
                                             client.logged_in_name,
                                             client.server_rank)
                
                else:
                    message = message.format(user, client.logged_in)
                
                self.server.message_user(user, self.name, message)
    
    # Channel moderation commands
    
    def cmd_kick(self, channel, user):
        # Force a user to leave a channel.
        if not self.test_crank(channel, 3): return
        
        user_id = self.server.get_id(user)
        if user_id in self.server.channel_cache[channel]:
            self.server.users[user_id].cmd_part(channel)
    
    def cmd_ban(self, channel, user):
        # Keep a user from entering this channel.
        if not self.test_crank(channel, 2): return
        
        self.server.channel_data[channel]['blacklist'].append(user)
        
        user_id = self.server.get_id(user)
        if user in self.server.channel_cache[channel]:
            self.server.users[user_id].cmd_part(channel)
    
    def cmd_unban(self, channel, user):
        # Unban a user from a channel.
        if not self.test_crank(channel, 2): return
        
        self.server.channel_data[channel]['blacklist'].remove(user)
    
    def cmd_promote(self, channel, user):
        # Increase a user's rank.
        if not self.test_crank(channel, 2): return
        
        channel_data = self.server.channel_data[channel]
        if user not in channel_data['ranked']:
            channel_data['ranked'][user] = 5
        
        if channel_data['ranked'][user] <= 2:
            return
        
        channel_data['ranked'][user] -= 1
    
    def cmd_demote(self, channel, user):
        # Decrease a user's rank.
        if not self.test_crank(channel, 2): return
        
        channel_data = self.server.channel_data[channel]
        if user not in channel_data['ranked']:
            channel_data['ranked'][user] = 5
        
        if channel_data['ranked'][user] <= 2:
            return
        
        channel_data['ranked'][user] += 1
    
    # Server moderation commands
    
    def cmd_server_kick(self, user):
        # Force a user to leave the server/plugin.
        if not self.test_srank(4): return
        
        self.functions['leave-plugin']('chat4')
    
    def cmd_server_ban(self, user):
        # Ban a user from using this server/plugin.
        pass
    
    def cmd_server_unban(self, user):
        # Unban a user.
        pass
    
    def cmd_server_forcekill(self, user):
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
        if not self.test_srank(2): return
        
        for client in self.server.users:
            client = self.server.users[client]
            if client.name == user:
                client.name = new_name
                for channel in self.channel_ranks:
                    self.response_common(channel, 'rename',
                                         user, new_name)
                break
    
    def cmd_disable_name(self, user):
        # Disable name changing for a user.
        if not self.test_srank(2): return
        
        for client in self.server.users:
            client = self.server.users[client]
            if client.name == user:
                client.name_change = False
                break
    
    def cmd_enable_name(self, user):
        # Enable name changing for a user.
        if not self.test_srank(2): return
        
        for client in self.server.users:
            client = self.server.users[client]
            if client.name == user:
                client.name_change = True
                break
    
    # Info commands
    
    def cmd_list(self, channel):
        # List who is in the channel.
        users = self.server.channel_cache[channel]
        users = ', '.join(users)
        message = 'User\'s in {0}: '.format(channel, users)
        
        message = message[:2] + '.'
        self.server.message_user('ServerNinja', self.name, message)
    
    def cmd_help(self):
        # Send a help message.
        pass
    
    # Censor, keeps language clean. :)
    def censor(self, message): # TODO: Make a censor..
        return message
    
    # Common messages
    def response_error(self, message_type=None):
        """Return a common error message."""
        
        if message_type == None:
            message = 'Undefined error.'
            
        # Access denied
        elif message_type == 'access denied':
            message = 'You do not have access to this feature.'
        
        # Not in channel
        elif message_type == 'not in channel':
            message = 'You are not in that channel!'
        
        # Can't change name
        elif message_type == 'name disabled':
            message = 'You are not allowed to change your name.'
        
        # Muted
        elif message_type == 'muted':
            message = 'You are muted.'
        
        # No such user
        elif message_type == 'no such user':
            message = 'There is no such user by that name.'
        
        # Not whitelisted
        elif message_type == 'whitelist':
            message = 'You are not whitelisted.'
        
        # Blacklisted
        elif message_type == 'blacklist':
            message = 'You are blacklisted.'
        
        elif message_type == 'logged in':
            message = 'You are already logged in.'
        
        elif message_type == 'login failed':
            message = 'Login failed.'
        
        self.server.message_user('ServerNinja', self.name, message)
    
    def response_common(self, channel, message_type, *args):
        # Return a common message.
        
        if message_type == None:
            message = 'Something happened.'
        
        # Joined a channel
        elif message_type == 'join':
            message = '{0} joined the channel {1}.'.format(*args)
        
        # Left a channel
        elif message_type == 'part':
            message = '{0} left the channel {1}.'.format(*args)
        
        # Renamed
        elif message_type == 'rename':
            message = '{0} renamed to {1}.'.format(*args)
        
        # Logged in
        elif message_type == 'login':
            message = '{0} logged in as {1}.'.format(*args)
        
        # Promoted
        elif message_type == 'promote':
            message = '{0} has been promoted to {1}.'.format(*args)
        
        # Demoted
        elif message_type == 'demote':
            message = '{0} has been demoted to {1}.'.format(*args)
        
        # Kicked
        elif message_type == 'kick':
            message = '{0} has been kicked by {1}.'.format(*args)
        
        # Banned
        elif message_type == 'ban':
            message = '{0} has been banned by {1}.'.format(*args)
        
        # Muted
        elif message_type == 'part':
            message = '{0} has been muted by {1}.'.format(*args)
        
        # Force-killed
        elif message_type == 'killed':
            message = '{0} was just owned by {1}.'.format(*args)
        
        self.server.message_channel(channel, message)
