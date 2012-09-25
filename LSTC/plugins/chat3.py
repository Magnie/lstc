# Chat.PY 3.0
# By: Magnie

import threading
import random
import cPickle

from time import strftime
import time


class Server(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.users = {} # Online users.
        
        # Accounts that have been made. 'username' : ['random, plain
        # text password', 'access_level']
        self.accounts = {'root' : ['n74w8nf2', '*']}
        self.banned = []
        
        # Channel ranks. 'channel' : {'user' : 'rank'}
        self.channel_data = {'scratch' : {'ranked' : {'Magnie' : '*'},
                                          'whitelist' : ['Magnie'],
                                          'blacklist' : [],
                                          'mutelist': [],
                                          'flags' : 'b',
                                          'motd' : 'Welcome!'}}
        
        # Characters for the pseudo-random passwords.
        self.passcase = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPAS\
DFGHJKLZXCVBNM'
        
        # Load data from saved files.
        self.load_accounts()
        self.load_channels()
        self.load_list()
        
        # Allow logging/debug mode?
        self.debug = 1
        
        # Help Desk Messages, not finished.
        self.help_desk = {'help': '''This is the help screen. These
categories available: basic, channel, mod, owner''',
                          'basic': '''These are the basic commands:
'''}
    
    def run(self):
        # Run any continual scripts here, along side the main server.
        pass
        
    
    # Messages from server
    
    def new_user(self, user_id, functions):
        # The functions dictionary contains the necessary functions
        # to send sensor-updates and broadcasts.
        
        # A new user has loaded this plugin,
        # create a "profile" for it.
        self.users[user_id] = User(functions, self)
        
        # Give them a name.
        name = 'User{0}'.format(user_id)
        self.users[user_id].name = name
        
        # Send a welcome message.
        message = 'Welcome {0} to the official Chat.PY 3.0 server!'
        message = message.format(name)
        self.user_message(name, message)
    
    def lost_user(self, user_id):
        try:
            # A user has decided to disconnect. Remove them.
            user = self.users[user_id]
            user.dead = True
            for chan in user.channels:
                user.part_channel(chan)
        
            del self.users[user_id]
        
        except KeyError:
            pass
    
    def new_message(self, user_id, message):
        # Received a message from the client.
        self.users[user_id].new_message(message)
    
    def disconnect(self):
        # The main server is turning off this plugin.
        self.server_message("Server is shutting down!")
        del self.users
    
    
    # Outbound messaging.
    
    # server_message sends a message to all users on the server.
    def server_message(self, message):
        message = '[{0}] {1}'.format(strftime('%H:%M:%S'), message)
        log('global', message)
        for user_id in self.users:
            try:
                # Update the sensor value for 'chat' to 'message'.
                self.users[user_id].send_sensor('chat', message)
            
                # Update who it was from.
                self.users[user_id].send_sensor('from', 'ServerNinja')
            
                # Tell the Scratch program that there is a new message.
                self.users[user_id].send_broadcast('_chat_update')
            
            except Exception:
                # If there is an error for some reason, then remove
                # them so it doesn't cause problems later.
                self.lost_user(user_id)
    
    # channel_message sends a message to all those in a channel.
    def channel_message(self, channel, message):
        message = '[{0}] {1}'.format(strftime('%H:%M:%S'), message)
        log(channel, message)
        for user_id in self.users:
            try:
                if channel in self.users[user_id].channels:
                    self.users[user_id].send_sensor('chat', message)
                    self.users[user_id].send_sensor('from', channel)
                    self.users[user_id].send_broadcast('_chat_update')
            
            except Exception:
                self.lost_user(user_id)
    
    # user_message sends a message to a specific user.
    def user_message(self, name, message):
        message = '[{0}] {1}'.format(strftime('%H:%M:%S'), message)
        log('user_messages', message)
        for user_id in self.users:
            try:
                if self.users[user_id].name == name:
                    self.users[user_id].send_sensor('chat', message)
                    self.users[user_id].send_sensor('from', 'PM')
                    self.users[user_id].send_broadcast('_chat_update')
                    break
            
            except KeyError:
                self.lost_users(user_id)
    
    
    # Account management
    
    def load_accounts(self):
        # Try and load the accounts, if they don't exist, create it.
        try:
            acc_file = open('accounts.chat', 'r')
            self.accounts = {}
            self.accounts = cPickle.load(acc_file)
            acc_file.close()
        
        except IOError, e:
            print e
            acc_file = open('accounts.chat', 'w')
            cPickle.dump(self.accounts, acc_file)
            acc_file.close()
    
    def save_accounts(self):
        acc_file = open('accounts.chat', 'w')
        cPickle.dump(self.accounts, acc_file)
        acc_file.close()
    
    # Channel management
    
    def load_channels(self):
        # Try and load the channels, if they don't exist, create it.
        try:
            chan_file = open('channels.chat', 'r')
            self.channel_data = {}
            self.channel_data = cPickle.load(chan_file)
            chan_file.close()
        
        except IOError, e:
            print e
            chan_file = open('channels.chat', 'w')
            cPickle.dump(self.channel_data, chan_file)
            chan_file.close()
    
    def save_channels(self):
        chan_file = open('channels.chat', 'w')
        cPickle.dump(self.channel_data, chan_file)
        chan_file.close()
    
    
    # Censor Words
    
    def load_list(self):
        try:
            list_file = open('badwords.txt', 'r')
            self.badwords = []
            self.badwords = list_file.read().split('\r\n')
            list_file.close()
        
        except IOError, e:
            print e
            list_file = open('badwords.chat', 'w')
            list_file.write('')
            list_file.close()
            self.badwords = []
    
    def save_list(self):
        list_file = open('badwords.chat', 'w')
        for line in self.badwords:
            list_file.writeline(line)
        list_file.close()
        


class User(object):
    
    def __init__(self, function, server):
        self.name = None
        
        # Authentication stuff.
        self.server_level = '-'
        self.auth_name = 'no one'
        
        self.channels = []
        
        self.server = server
        
        # Communication Functions retrieved from the Client class of
        # the server program.
        self.send_broadcast = function['send_broadcast']
        self.send_sensor = function['send_sensor']
        
        # IP ban and unban functions.
        self.ban_user = function['ban_user']
        self.unban_user = function['unban_user']
        self.ip = function['ip']
        self.force_leave = function['force_leave']
        
        self.log = []
        
        # Restrict how fast messages are sent.
        self.last_sent = 0
        self.message_limit = 4
        self.message_current = 0
        self.limit_hit = 0
        self.max_hits = 5
        self.temp_silence = 0
        
        self.dead = False # Don't send to me if dead.
        self.channel = None # The "current" channel.
    
    def new_message(self, message):
        
        if time.time() <= self.temp_silence:
            return
        
        if time.time() < (self.last_sent + 3):
            if self.message_current >= self.message_limit:
                self.message_current = 0
                self.limit_hit += 1
                self.last_sent = time.time()
                
                if self.limit_hit >= self.max_hits:
                    for user_id in self.server.users:
                        user = self.server.users[user_id]
                        if user.name == self.name:
                            message = "Auto-Kicked for spamming."
                            self.server.user_message(self.name, message)
                            time.sleep(0.1)
                            self.force_leave()
                            self.server.lost_user(user_id)
                
                self.temp_silence = time.time() + 5
                message = "You have been silenced for five seconds."
                self.server.user_message(self.name, message)
                return
            
            self.message_current += 1
        
        else:
            self.last_sent = time.time()
            self.message_current = 0
        
        
        # Split the command/request from the arguments/options.
        message_split = message.split(':', 1)
        cmd = message_split[0]
        
        args = 'N/A'
        if len(message_split) == 2:
            args = message_split[1]
        
        # Log for debugging reasons.
        if self.server.debug == 1:
            self.log.append(message)
        
        if cmd == 'send':
            self.channel, chat_message = args.split(':', 1)
            
            # Allows forward-slash commands like normal IRC.
            # Makes it easier to program the client.
            if chat_message[0] != '/':
                self.send_chat(self.channel, chat_message)
            
            else:
                message_split = chat_message.split(' ', 1)
                cmd = message_split[0][1:]
        
                if len(message_split) == 2:
                    args = message_split[1]
        
        # Allows you to change your name.
        if cmd == 'name':
            args = args.split(' ')
            self.change_name(args[0])
        
        # Join multiple channels.
        elif cmd == 'join':
            if args:
                self.join_channel(args)
        
        # Leave any extra channels.
        elif cmd == 'part':
            if args:
                self.part_channel(args)
        
        elif cmd == 'help':
            self.get_help()
        
        # Authenticate to give you access to more commands.
        elif cmd == 'auth':
            args = args.split(' ')
            self.login_account(args[0], args[1])
        
        # Authenticate via Scratch to give you access to more commands.
        elif cmd == 'login':
            args = args.split(' ')
            self.scratch_auth(args[0], args[1])
        
        # Create an account to use.
        elif cmd == 'create':
            self.create_account(args)
        
        # whois such and such?
        elif cmd == 'whois':
            self.whois_user(args)
        
        # Switching accounts, or for testing.
        elif cmd == 'logout':
            self.logout_account()
        
        # Displays debugging info.
        elif cmd == 'data':
            data_message = """Name = {0}
Server Level = {1}
Channels = {2}
Message Log: {3}""".format(self.name,
                           self.server_level,
                           self.channels,
                           self.log)
            self.server.user_message(self.name, data_message)
        
        # Send a personal message.
        elif cmd == 'pm':
            args = args.split(' ', 1)
            self.whisper(args[0], args[1])
        
        # Mod, Admin, Owner commands
        
        # Ban an IP.
        elif cmd == 'ban':
            self.ban_user(args)
        
        # Unban an IP.
        elif cmd == 'unban':
            self.unban_user(args)
        
        # Get the IP of a user.
        elif cmd == 'get-ip':
            self.get_ip(args)
        
        # Silence someone
        elif cmd == 'mute':
            self.mute_user(self.channel, args)
        
        # Unmute someone
        elif cmd == 'unmute':
            name = args[0]
            self.unmute_user(self.channel, args)
        
        # Set a user's server_level
        elif cmd == 'srank':
            args = args.split(' ')
            self.set_srank(args[0], args[1])
        
        # Set a users' channel_level
        elif cmd == 'crank':
            args = args.split(' ')
            self.set_crank(self.channel, args[0], args[1])
        
        # List all users in a channel.
        elif cmd == 'list':
            if self.channel:
                args = self.channel
            
            self.list_users(args)
        
        # List all users online.
        elif cmd == 'list-all':
            self.list_all_users()
        
        # List all created channels.
        elif cmd == 'list-channels':
            self.list_channels()
        
        # Blacklist user
        elif cmd == 'blacklist':
            args = args.split(' ')
            # Command, Channel, Name
            self.blacklist(args[0], args[1], args[2])
        
        # Whitelist user
        elif cmd == 'whitelist':
            args = args.split(' ')
            # Command, Channel, Name
            self.whitelist(args[0], args[1], args[2])
        
        # Kick a user from a room.
        elif cmd == 'kick':
            # Channel, username
            self.kick_user(self.channel, args)
        
        # Force a user to disconnect from chat3.
        elif cmd == 'force-kill':
            self.force_kill(args)
        
        # Set the motd of a channel.
        elif cmd == 'motd':
            args = args.split(' ')
            channel = args[0]
            args = ' '.join(args[1:])
            self.set_motd(channel, args)
        
        # Set the flags of a channel.
        elif cmd == 'flags':
            args = args.split(' ')
            channel = args[0]
            args = ' '.join(args[1:])
            self.set_flags(channel, args)
        
        # Send a global message all over the server.
        elif cmd == 'serverninja':
            self.global_message(args)
        
        # Force a user to rename.
        elif cmd == 'rename':
            args = args.split(' ')
            self.force_rename(args[0], args[1])
            
    
    # Basic Command functions.
    
    def send_chat(self, channel, message):
        
        # Makes sure a user isn't sending a message to a channel
        # they aren't in.
        if channel not in self.channels:
            message = "You aren't in {0}!".format(channel)
            self.server.user_message(self.name, message)
            return
        
        # Make sure they aren't muted.
        channel_tmp = self.server.channel_data[channel]
        if self.server_level == '#':
            message = "You are muted."
            self.server.user_message(self.name, message)
            return
        
        elif self.name in channel_tmp['mutelist']:
            message = "You are muted."
            self.server.user_message(self.name, message)
            return
        
        channel_level = '-'
        if self.auth_name != 'no one':
            if self.auth_name in channel_tmp['ranked']:
                channel_level = channel_tmp['ranked'][self.name]
        
        message = '{0}{1}: {2}'.format(channel_level,
                                       self.name,
                                       message)
        message = self.censor(message)
        self.server.channel_message(channel, message)
    
    def change_name(self, name):
        # Make sure two users don't have the same name.
        change = 1
        for user in self.server.users:
            user = self.server.users[user]
            if user.name == name:
                change = 0
                break
            
        if change == 0: # Don't change their name.
            message = "{0} is already in use.".format(name)
            self.server.user_message(self.name, message)
        
        elif change == 1: # Do change their name.
            old_name = self.name
            self.name = name
            message = "{0} renamed to {1}.".format(old_name, name)
            for channel in self.channels:
                self.server.channel_message(channel, message)
    
    def join_channel(self, channel):
        if channel in self.server.channel_data:
            channel_tmp = self.server.channel_data[channel]
            
            if 'b' in channel_tmp['flags']:
                if self.name in channel_tmp['blacklist']:
                    message = 'You are unable to join {0}.'
                    message = message.format(channel)
                    self.server.user_message(self.name, message)
                    return
            
            elif 'w' in channel_tmp['flags']:
                if self.name not in channel_tmp['whitelist']:
                    message = 'You are unable to join {0}.'
                    message = message.format(channel)
                    self.server.user_message(self.name, message)
                    return
            
            elif 'r' in channel_tmp['flags']:
                if self.server_level not in channel_tmp['ranks']:
                    message = 'You are unable to join {0}.'
                    message = message.format(channel)
                    self.server.user_message(self.name, message)
                    return
        
        else:
            channel_settings = {'ranked' : {self.name : '^'},
                                'whitelist' : [self.name],
                                'blacklist' : [],
                                'mutelist': [],
                                'flags' : 'b',
                                'motd' : 'New Channel!'}
            self.server.channel_data[channel] = channel_settings
        
        if len(channel) > 10:
            message = 'Channel names have a '
            message += 'maximum length of 10 characters.'
            self.server.user_message(self.name, message)
            return
        
        self.channels.append(channel)
        
        message = '{0} has joined channel {1}!'
        message = message.format(self.name, channel)
        self.server.channel_message(channel, message)
        
        time.sleep(0.2)
        
        message = self.server.channel_data[channel]['motd']
        self.server.user_message(self.name, message)
        
        self.send_sensor('channel', channel)
        self.send_broadcast('_chat_joined')
    
    def part_channel(self, channel):
        # Who wouldn't want to leave a boring channel?
        if channel not in self.channels:
            message = 'You aren\'t in {0}!'
            message = message.format(channel)
            self.server.user_message(self.name, message)
            return
        
        self.channels.remove(channel)
        
        message = '{0} has left channel {1}!'
        message = message.format(self.name, channel)
        self.server.channel_message(channel, message)
        
        if self.dead:
            return
        
        message = 'You have left channel {0}!'
        message = message.format(channel)
        self.server.user_message(self.name, message)
        
        self.send_sensor('channel', channel)
        self.send_broadcast('_chat_left')
    
    
    # Account Management
    
    def create_account(self, username):
        
        # Make sure they don't "duplicate" an account.
        if username in self.server.accounts:
            message = '{0} has already been created.'
            message = message.format(username)
            self.server.user_message(self.name, message)
            return
        
        
        # Create a random password for the user so it won't matter
        # if the admins have the users' password, they can't do
        # anything with it.
        case_length = len(self.server.passcase)
        password = ''
        for x in xrange(0, 7):
            i = random.randrange(0, case_length)
            password += self.server.passcase[i]
        
        self.server.accounts[username] = [password, '+']
        
        message = "Account created and logged in!\n"
        message += "Username: {0}\nPassword: {1}"
        message = message.format(username, password)
        self.server.user_message(self.name, message)
        
        self.server.save_accounts()
    
    def login_account(self, username, password):
        # Make sure the user isn't already logged in.
        if self.auth_name != 'no one':
            message = "You are already logged in!"
            self.server.user_message(self.name, message)
            return
        
        # Make sure the account exists.
        if username in self.server.accounts:
            # Check the passwords.
            if password == self.server.accounts[username][0]:
                self.server_level = self.server.accounts[username][1]
                self.auth_name = username
        
        # If self.server_level changed, then they've been logged in,
        # otherwise they failed to.
        if self.server_level != '-':
            message = "You have logged in as {0}!"
            message = message.format(username)
            self.server.user_message(self.name, message)
            
        else:
            message = "Wrong username or password!"
            self.server.user_message(self.name, message)
    
    def scratch_auth(self, username, password, uid):
        # Make sure the user isn't already logged in.
        if self.auth_name != 'no one':
            message = "You are already logged in!"
            self.server.user_message(self.name, message)
            return
        
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
                if username not in self.server.accounts:
                    self.server.accounts[username] = [None, '+']
                
                self.server_level = self.server.accounts[username][1]
                self.auth_name = username
    
    def whois_user(self, name):
        for user_id in self.server.users:
            user = self.server.users[user_id]
            if user.name == name:
                message = '{0} is logged in as {1}, with level {2}.'
                message = message.format(name,
                                         user.auth_name,
                                         user.server_level)
                self.server.user_message(self.name, message)
                break
    
    def logout_account(self):
        # Reset the server_level
        self.server_level = '-'
        self.auth_name = 'no one'
        self.server.user_message(self.name, 'Logged out.')
    
    
    # Ranked User Commands
    
    def global_message(self, message):
        if self.server_level not in '*~':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        message = self.censor(message)
        message = 'ServerNinja: ' + message
        self.server.server_message(message)
    
    def get_ip(self, name):
        if self.server_level not in '~*':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        for user in self.server.users:
            if self.server.users[user].name == name:
                message = '{0}\'s IP is {1}.'
                message = message.format(name, self.server.users[user].ip)
                self.server.user_message(self.name, message)
                break
    
    def mute_user(self, channel, name):
        channel = self.server.channel_data[channel]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level in '*~^@' or self.server_level in '*~^@':
            channel['mutelist'].append(name)
        
        else:
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
    
    def unmute_user(self, channel, name):
        channel = self.server.channel_data[channel]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level in '*~^@' or self.server_level in '*~^@':
            channel['mutelist'].remove(name)
        
        else:
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
    
    def set_srank(self, account, new_rank):
        if self.server_level not in '*~':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        if account in self.server.accounts:
            if self.server_level in '~':
                if new_rank in '*~':
                    return
            
            self.server.accounts[account][1] = new_rank
            self.server.save_accounts()
            
            message = "Updated Server Rank for {0} to {1}."
            message = message.format(account, new_rank)
            self.server.user_message(self.name, message)
    
    def set_crank(self, channel, account, new_rank):
        channel = self.server.channel_data[channel]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level in '^' or self.server_level in '*~':
            channel['ranked'][account] = new_rank
            message = "Updated Channel Rank for {0}."
            message = message.format(account)
            self.server.user_message(self.name, message)
            self.server.save_channels()
        
        else:
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
    
    def force_kill(self, name):
        if self.server_level not in '*~':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        for user_id in self.server.users:
            user = self.server.users[user_id]
            if user.name == name:
                user.force_leave()
                self.server.lost_user(user_id)
                break
        
        message = "{0} has been forced to leave chat3."
        message = message.format(name)
        self.server.user_message(self.name, message)
    
    def blacklist(self, cmd, channel, name):
        channel = self.server.channel_data[channel]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level not in '*~^':
            message = 'You don\'t have access to this.'
            self.server.user_message(self.name, message)
            return
        
        if cmd == 'add':
            channel['blacklist'].append(name)
            message = 'Added {0} to blacklist.'
            message = message.format(name)
            self.server.user_message(self.name, message)
        
        elif cmd == 'rem':
            channel['blacklist'].remove(name)
            message = 'Removed {0} from blacklist.'
            message = message.format(name)
            self.server.user_message(self.name, message)
    
    def whitelist(self, cmd, channel, name):
        channel = self.server.channel_data[channel]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level not in '*~^':
            message = 'You don\'t have access to this.'
            self.server.user_message(self.name, message)
            return
        
        if cmd == 'add':
            channel['whitelist'].append(name)
            message = 'Added {0} to whitelist.'
            message = message.format(name)
            self.server.user_message(self.name, message)
        
        elif cmd == 'rem':
            channel['whitelist'].remove(name)
            message = 'Removed {0} from whitelist.'
            message = message.format(name)
            self.server.user_message(self.name, message)
    
    def set_flags(self, channel, args):
        channel = self.server.channel_data[channel]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level not in '*~^':
            message = 'You don\'t have access to this.'
            self.server.user_message(self.name, message)
            return
        
        channel['flags'] = args
        self.server.save_channels()
    
    def set_motd(self, channel_name, motd):
        channel = self.server.channel_data[channel_name]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level not in '*~^':
            message = 'You don\'t have access to this.'
            self.server.user_message(self.name, message)
            return
        
        channel['motd'] = motd
        message = 'MOTD set to: ' + motd
        self.server.channel_message(channel_name, message)
        self.server.save_channels()
    
    def kick_user(self, channel_name, account):
        channel = self.server.channel_data[channel_name]
        if self.auth_name in channel['ranked']:
            channel_level = channel['ranked'][self.auth_name]
        
        else:
            channel_level = '-'
        
        if channel_level in '^@*~' or self.server_level in '*~':
            for user_id in self.server.users:
                user = self.server.users[user_id]
                if user.name == account:
                    user.part_channel(channel_name)
                    break
            
            message = "{0} has been kicked."
            message = message.format(account)
            self.server.user_message(self.name, message)
            
            message = "You have been kicked from {0}."
            message = message.format(channel_name)
            self.server.user_message(user.name, message)
        
        else:
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
    
    # Advanced User Commands
    
    def whisper(self, to_user, message):
        if self.server_level not in '*~^@%+':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        new = '{0} > {1}: {2}'
        message = new.format(self.name, to_user, message)
        self.server.user_message(to_user, message)
        self.server.user_message(self.name, message)
    
    def list_users(self, channel):
        users = []
        for user_id in self.server.users:
            user = self.server.users[user_id]
            if channel in user.channels:
                users.append(user.name)
        
        
        message = 'Users in {0}: ' + ', '.join(users)
        message = message.format(channel)
        self.server.user_message(self.name, message)
    
    def list_all_users(self):
        message = ''
        for user_id in self.server.users:
            user = self.server.users[user_id]
            message += ', ' + user.name
        
        message += '.'
        message = 'Users online: ' + message[2:]
        self.server.user_message(self.name, message)
    
    def list_channels(self):
        message = ''
        for channel in self.server.channel_data:
            message += ', ' + channel
        
        message += '.'
        message = 'Created channels: ' + message[2:]
        self.server.user_message(self.name, message)
    
    def list_accounts(self):
        if self.server_level not in '*~':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        message = ''
        for user in self.server.accounts:
            message += ', ' + user
        
        message += '.'
        message = 'Created Accounts: ' + message[2:]
        self.server.user_message(self.name, message)
    
    def force_rename(self, name, new_name):
        if self.server_level not in '*~':
            message = "You do not have access to this."
            self.server.user_message(self.name, message)
            return
        
        for user_id in self.server.users:
            user = self.server.users[user_id]
            if user.name == name:
                user.change_name(new_name)
                break
        
    
    # "Accessories"
    
    def censor(self, raw_message):
        message = raw_message.split(' ')
        print message
        
        new_message = ''
        for word in message:
            if word in self.server.badwords and word != '':
                word = "*ponies*"
            
            new_message += ' ' + word
        
        print new_message
        return new_message[1:]
    
    def get_help(self, item='help'):
        #message = self.server.help_desk[item]
        message = '''Basic Commands:
/name [new_name] - Change your name to [name]
/join [channel] - Join [channel].
/part [channel] - Leave [channel].
/list [channel] - List users in channel.
/data - List advanced info about yourself.
/help - Display this info.

Advanced Commands:
/create [username] - Creates an account on the server.
/auth [username] [password] - Login to an account.
/logout - Logout of your account.
/whois [username] - Get some details about a user.
/list-all - List all users on the server.
/list-channels - List all channels on the server.

Channel Commands:
/mute [name] - Mutes a user.
/unmute [name] - Unmutes a user.
/crank [channel] [name] [new_rank] - Change a user's rank.
/blacklist [add/rem] [channel] [name] - Add or remove a user from the blacklist.
/whitelist [add/rem] [channel] [name] - Add or remove a user from the whitelist.
/kick [channel] [name] - Force a user to leave a channel.
/motd [channel] [message] - Set the welcome message for a channel.
/flags [channel] [flags] - Set the flags for a channel.

Mod Commands:
/get-ip [name] - Get the IP of a user.
/ban [ip] - Ban this IP.
/unban [ip] - Unban this IP.
/rename [name] [new name] - For a user to rename.

Admin Commands:
/srank [account] [new_rank] - Change the server rank of a user.
/force-kill [name] - Force a user to disconnect from the server.'''
        self.server.user_message(self.name, message)

def log(fn, string):
    string = str(string)
    try:
        log_file = open(fn + '.log', 'a')
        log_file.write('\n' + string)
        log_file.close()
    except IOError, e:
        log_file = open(fn + '.log', 'w')
        log_file.write(string)
        log_file.close()
