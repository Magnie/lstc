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
import cPickle
import urllib
import os

from time import strftime


DIRECTORY = 'chat4'

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
        self.owner = 'Magnie'
        
        self.users = {}
        
        self.ranks = ['Owner', 'Admin', 'Operator', 'Half-Op',
                      'Voice', 'Normal', 'Shunned']
        
        self.scratch_login = False
        
        self.channel_data = load_data('channels.txt')
        
        if not self.channel_data:
            self.channel_data = {'scratch' : {'ranked': {self.owner : 0},
                                              'whitelist': [self.owner],
                                              'blacklist': set([]),
                                              'mutelist': set([]),
                                              'flags': 'bp',
                                              'motd': 'Welcome!'}}
            save_data('channels.txt', self.channel_data)
        
        
        self.channel_cache = {} # channel : [users]
        for channel in self.channel_data:
            self.channel_cache[channel] = set([])
        
        self.account_data = load_data('accounts.txt')
        if not self.account_data:
            self.account_data = {self.owner: 0}
            save_data('accounts.txt', self.account_data)
        
        self.login_data = load_data('logins.txt')
        if not self.login_data:
            self.login_data = {self.owner: '123'}
            save_data('logins.txt', self.login_data)
        
        self.banned_accounts = set([])
        self.banned_names = set(['ServerNinja'])
        
        self.chat_version = 4.0;
    
    def run(self):
        pass
    
    def new_user(self, user_id, functions):
        self.users[user_id] = Client(functions, self)
    
    def lost_user(self, user_id):
        user = self.users[user_id]
        channels = user.channel_ranks
        for channel in list(channels):
            user.cmd_part(channel)
        
        del self.users[user_id]
    
    def new_message(self, user_id, message):
        if user_id not in self.users:
            print "User {0} does not exist on chat4.py".format(user_id)
            return
        self.users[user_id].new_message(message)
    
    def disconnect(self):
        self.message_server("Plugin is being restarted, please wait five "\
                            "seconds and then click the green flag.")
    
    # Functions
    
    def get_id(self, name):
        for user_id in self.users:
            if self.users[user_id].name == name:
                return user_id
        
        return None
    
    def kill_user(self, name):
        user_id = self.get_id(name)
        self.users[user_id].functions['force-kill']()
    
    # Message functions
    
    def message_server(self, message):
        # Send message to every user on the server.
        for user_id in self.users:
            user = self.users[user_id]
            self.message_send('ServerNinja', user, message)
        
        append_log("server.txt", message)
    
    def message_channel(self, channel, message):
        # Send message to only people in a specific channel.
        if channel not in self.channel_cache:
            return
        
        for user_id in self.channel_cache[channel]:
            user = self.users[user_id]
            self.message_send(channel, user, message)
        
        fn = 'chn_' + channel + '.txt'
        append_log(fn, message)
    
    def message_user(self, from_user, user_name, message):
        # Send message to a specific person.
        for user_id in self.users:
            user = self.users[user_id]
            if user.name == user_name:
                self.message_send(from_user, user, message)
                break
        
        # Don't save messages from ServerNinja.
        if from_user == 'ServerNinja': return
        
        fn = 'pm_' + from_user + '_' + user_name + '.txt'
        append_log(fn, message)
    
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
    
    # Avatar functions
    def update_avatar(self, channel, avatar):
        # Will send update to all users in a channel that have avatar chat
        # enabled.
        pass


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
        
        self.channels = set([])
        self.channel = 'none'
        
        self.name_change = True
        self.char_chat = False
        
        # Report log for sending a full report.
        self.report_log = []
        
        # Character Positions
        self.x_pos = 0
        self.y_pos = 0
        
        # Access to server class functions
        self.server = server
        
        message = ("Welcome to Chat.PY 4.0! If you are seeing this "
                   "then you are connected to the server!")
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
        
        elif cmd == 'flags':
            args = args.split(' ', 1)
            if len(args) == 2: # /flags [channel] [options]
                self.cmd_flags(args[0], args[1])
            
            else: # /flags [options]
                self.cmd_flags(self.channel, args[0])
        
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
            args = args.split(' ', 1)
            if len(args) == 2:
                # args = [channel, username, mod]
                self.cmd_promote(args[0], args[1])
            
            else:
                self.cmd_promote(self.channel, args[0])
        
        elif cmd == 'demote':
            args = args.split(' ', 2)
            if len(args) == 3:
                # args = [channel, username, mod]
                self.cmd_demote(args[0], args[1])
        
        elif cmd == 'list':
            if args:
                # args = channel
                self.cmd_list(args)
            
            else:
                self.cmd_list(self.channel)
        
        elif cmd == 'motd':
            args = args.split(' ', 1)
            if len(args) == 2:
                # args = [channel, msg]
                self.cmd_motd(args[0], args[1])
        
        elif cmd == 'help':
            self.cmd_help()
        
        # Use character chat?
        elif cmd == 'character':
            if args == 'True':
                self.char_chat = True
            
            else:
                self.char_chat = False
        
        # Report abusive message/conversation
        elif cmd == 'report':
            if args:
                # args = channel
                self.cmd_report_abuse(args)
        
        # Server moderation
        elif cmd == 'server':
            args = args.split(' ', 1)
            sub = args[0]
            args = ' '.join(args[1:])
            
            if sub == 'kick':
                self.cmd_server_kick(args)
            
            elif sub == 'ban':
                self.cmd_server_ban(args)
            
            elif sub == 'unban':
                self.cmd_server_unban(args)
            
            elif sub == 'promote':
                args = args.split(' ', 2)
                if len(args) == 2:
                    # args = [username, mod]
                    self.cmd_server_promote(args[0], args[1])
            
            elif sub == 'demote':
                args = args.split(' ', 2)
                if len(args) == 2:
                    # args = [username, mod]
                    self.cmd_server_demote(args[0], args[1])
            
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
        #if self.test_srank(1): return True
        
        if not self.logged_in:
            return False
        
        if self.channel_ranks[channel] <= rank:
            return True
        
        return False
    
    # Command functions
    # Avatar Chat Functions
    def cmd_update_location(self, x, y):
        # Updates the position of the avatar and sends it to everyone.
        self.x_pos = x
        self.y_pos = y
    
    # Basic chat commands.
    
    def cmd_send(self, channel, message):
        # Send a message to a channel
        if channel not in self.channel_ranks:
            self.response_user('not in channel')
            return
        
        if self.channel_ranks[channel] == 'mute':
            self.response_user('muted')
            return
            
        full_message = '{0}: {1}'.format(self.name, message)
        full_message = self.censor(full_message)
        
        self.server.message_channel(channel, full_message)
    
    def cmd_pm(self, user, message):
        # Send a message to another user
        
        if not self.test_srank(4): return
        
        message = '{0} --> {1}: {2}'.format(self.name, user, message)
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
            self.server.channel_cache[channel] = set([])
        
        channel_data = self.server.channel_data[channel]
        # Check if the whitelist applies.
        if 'w' in channel_data['flags']:
            if self.logged_in_name not in channel_data['whitelist']:
                self.response_user(message_type='whitelist')
                return
        
        # Check if the blacklist applies.
        if 'b' in channel_data['flags']:
            if self.name in channel_data['blacklist']:
                self.response_user(message_type='blacklist')
                return
        
        if self.logged_in_name in channel_data['ranked']:
            name = channel_data['ranked'][self.logged_in_name]
            self.channel_ranks[channel] = name
        
        else:
            self.channel_ranks[channel] = 5
        
        user_id = self.functions['user-id']
        self.server.channel_cache[channel].add(user_id)
        self.channels.add(channel)
        
        self.server.message_user('ServerNinja', self.name,
                                 channel_data['motd'])
        
        self.send_sensor('channel', channel)
        self.send_broadcast('joined')
        self.response_common(channel, 'join', self.name, channel)
    
    def cmd_part(self, channel):
        # Leave a channel
        del self.channel_ranks[channel]
        user_id = self.functions['user-id']
        self.server.channel_cache[channel].remove(user_id)
        self.channels.remove(channel)
        
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
            self.response_user(message_type='name disabled')
            return
        
        if new_name in self.server.banned_names:
            return
        
        # Check if the name is already in use.
        if self.server.get_id(new_name):
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
            self.response_user(message_type='logged in')
            return
        
        if not self.server.scratch_login:
            login_data = self.server.login_data
            if scratch_user in login_data:
                if login_data[scratch_user] == scratch_password:
                    self.logged_in = True
                    self.logged_in_name = scratch_user
                    
                    accounts = self.server.account_data
                    if scratch_user in accounts:
                        # If the account exists, use the saved rank.
                        self.server_rank = accounts[scratch_user]
                
                    else:
                        # If the account doesn't exist, create it.
                        accounts[scratch_user] = 4
                        save_data('accounts.txt', self.server.account_data)
                
                    self.server_rank = accounts[scratch_user]
                    for channel in self.channels:
                        channel_data = self.server.channel_data[channel]
                        if self.logged_in_name in channel_data['ranked']:
                            name = channel_data['ranked'][self.logged_in_name]
                            self.channel_ranks[channel] = name
                
                    self.response_user('login successful')
            else:
                self.logged_in = True
                self.logged_in_name = scratch_user
                
                login_data[scratch_user] = scratch_password
                save_data('logins.txt', login_data)
                
                accounts = self.server.account_data
                if scratch_user in accounts:
                    # If the account exists, use the saved rank.
                    self.server_rank = accounts[scratch_user]
                
                else:
                    # If the account doesn't exist, create it.
                    accounts[scratch_user] = 4
                    save_data('accounts.txt', self.server.account_data)
                
                self.server_rank = accounts[scratch_user]
                for channel in self.channels:
                    channel_data = self.server.channel_data[channel]
                    if self.logged_in_name in channel_data['ranked']:
                        name = channel_data['ranked'][self.logged_in_name]
                        self.channel_ranks[channel] = name
                
                self.response_user('login successful')
                
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
            self.response_user(message_type='login failed')
            return
        
        else:
            result = result.split(':')
            if result[2] == 'blocked' or result[2] in banned:
                # Banned by the Scratch Team or banned just for this.
                self.response_user(message_type='login failed')
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
                    save_data('accounts.txt', self.server.account_data)
                
                self.server_rank = accounts[scratch_user]
                for channel in self.channels:
                    channel_data = self.server.channel_data[channel]
                    if self.logged_in_name in channel_data['ranked']:
                        name = channel_data['ranked'][self.logged_in_name]
                        self.channel_ranks[channel] = name
                
                self.response_user('login successful')
    
    def cmd_logout(self):
        # Deauthenticate
        self.logged_in = False
        self.logged_in_name = None
        self.server_rank = 5
        
        self.response_user('logout')
    
    def cmd_whois(self, user):
        for client in self.server.users:
            client = self.server.users[client]
            if client.name == user:
                message = 'Whois on {0}: \n'
                message += 'Logged in: {1} \n'
                if client.logged_in:
                    server_rank_name = self.server.ranks[client.server_rank]
                    message += 'Logged in as: {2}\n'
                    message += 'Server rank: {3} - {4}\n'
                    message += 'Channel Ranks: \n'
                    for channel in self.channel_ranks:
                        crank = self.channel_ranks[channel]
                        crank_name = self.server.ranks[crank]
                        message += '  {0}: {1} - {2}\n'.format(channel,
                                                             crank,
                                                             crank_name)
                    
                    message = message.format(user, client.logged_in,
                                             client.logged_in_name,
                                             client.server_rank,
                                             server_rank_name)
                    
                    if self.test_srank(1):
                        message += '\nIP Hash: {0}'.format(self.functions['ip-hash'])
                
                else:
                    message = message.format(user, client.logged_in)
                
                self.server.message_user(user, self.name, message)
    
    # Channel moderation commands
    def cmd_motd(self, channel, motd):
        # Change the channel Message of the Day.
        if not self.test_crank(channel, 3): return
        
        self.server.channel_data[channel]['motd'] = motd
        save_data('channels.txt', self.server.channel_data)
        
        self.response_common(channel, 'motd', self.name, motd)
    
    def cmd_flags(self, channel, flags):
        if not self.test_crank(3) and not self.test_srank(1): return
        
        if 'p' in flags and self.test_srank(1):
            flags = flags.replace('p', '')
        
        self.server.channel_data[channel]['flags'] = flags
        save_data('channels.txt', self.server.channel_data)
        
        self.response_common(channel, 'flags', flags)
    
    def cmd_kick(self, channel, user):
        # Force a user to leave a channel.
        if not self.test_crank(channel, 3): return
        
        user_id = self.server.get_id(user)
        if user_id in self.server.channel_cache[channel]:
            self.server.users[user_id].cmd_part(channel)
        
        self.response_common(channel, 'kick', user, self.name)
    
    def cmd_ban(self, channel, user):
        # Keep a user from entering this channel.
        if not self.test_crank(channel, 2) and not self.test_srank(1): return
        
        self.server.channel_data[channel]['blacklist'].add(user)
        
        user_id = self.server.get_id(user)
        if user in self.server.channel_cache[channel]:
            self.server.users[user_id].cmd_part(channel)
        
        self.response_common(channel, 'ban', user, self.name)
    
    def cmd_unban(self, channel, user):
        # Unban a user from a channel.
        if not self.test_crank(channel, 2) and not self.test_srank(1): return
        
        self.server.channel_data[channel]['blacklist'].remove(user)
        self.response_common(channel, 'unban', self.name, user)
    
    def cmd_promote(self, channel, user):
        # Increase a user's rank.
        if not self.test_crank(channel, 2) and not self.test_srank(1): return
        
        channel_data = self.server.channel_data[channel]
        if user not in channel_data['ranked']:
            channel_data['ranked'][user] = 5
        
        if channel_data['ranked'][user] != 0:
            channel_data['ranked'][user] -= 1
        
        save_data('channels.txt', self.server.channel_data)
    
    def cmd_demote(self, channel, user):
        # Decrease a user's rank.
        if not self.test_crank(channel, 2) and not self.test_srank(1): return
        
        channel_data = self.server.channel_data[channel]
        if user not in channel_data['ranked']:
            channel_data['ranked'][user] = 5
        
        if channel_data['ranked'][user] != len(self.server.ranks) - 1:
            channel_data['ranked'][user] += 1
        
        save_data('channels.txt', self.server.channel_data)
    
    # Server moderation commands
    def cmd_report_abuse(self, message):
        # Report this line as abusive or against the rules.
        
        report_type, reported_msg = message.split(':', 1)
        if report_type == 'start':
            date = strftime('%D/%M/%Y %h:%m:%s')
            self.report_log = ['Report starting at {0}.'.format(date)]
            self.report_log.append(message)
        
        elif report_type == 'end':
            date = strftime('%D/%M/%Y %h:%m:%s')
            self.report_log.append(message)
            self.report_log.append('Report ending at {0}'.format(date))
            
            save_log('report_{0}'.format(date), self.report_log)
        
        else:
            self.report_log.append(message)
        
        return
    
    def cmd_server_kick(self, user):
        # Force a user to leave the server/plugin.
        if not self.test_srank(4): return
        
        self.functions['leave-plugin']('chat4')
    
    def cmd_server_ban(self, ip_hash):
        # Ban a user from using this server/plugin.
        if not self.test_srank(1): return
        
        self.functions['server-ban'](ip_hash)
    
    def cmd_server_unban(self, ip_hash):
        # Unban a user.
        if not self.test_srank(1): return
        
        self.functions['server-unban'](ip_hash)
    
    def cmd_server_forcekill(self, user):
        # Force a user to disconnect from the server in whole.
        if not self.test_srank(1): return
        
        self.server.kill_user(user)
    
    def cmd_server_promote(self, user, mod):
        # Increase a user's rank on the server.
        if not self.test_srank(1): return
        
        if user in self.server.account_data:
            self.server.account_data[user] -= int(mod)
            
            if self.server.account_data[user] < 0:
                self.server.account_data[user] = 0
            
            self.server_rank = self.server.account_data[user]
        
        save_data('accounts.txt', self.server.account_data)
    
    def cmd_server_demote(self, user, mod):
        # Decrease a user's rank on the server.
        if not self.test_srank(1): return
        
        if user in self.server.account_data:
            self.server.account_data[user] += mod
            
            if self.server.account_data[user] > (len(self.server.ranks) - 1):
                self.server.account_data[user] = len(self.server.ranks) - 1
            
            self.server_rank = self.server.account_data[user]
        
        save_data('accounts.txt', self.server.account_data)
    
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
        cache = self.server.channel_cache[channel]
        # For user id in cache, append the name of that user.
        users = ', '.join([self.server.users[u].name for u in cache])
        message = 'User\'s in {0}: {1}'.format(channel, users)
        
        message += '.'
        self.server.message_user('ServerNinja', self.name, message)
    
    def cmd_help(self):
        # Send a help message.
        pass
    
    # Censor, keeps language clean. :)
    def censor(self, message): # TODO: Make a censor..
        return message
    
    # Common messages
    def response_user(self, message_type=None):
        """Return a common error message."""
        
        msg_types = {None : 'Undefined error/message.',
                     'access denied' : 'You do not have '
                                       'access to this feature.',
                     'not in channel' : 'You are not in that channel.',
                     'name disabled' : 'You are not allowed to '
                                       'change your name.'
                     }
        
        if message_type == None:
            message = 'Undefined error/message.'
        
        # Error Messages
          
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
        
        # Already logged in
        elif message_type == 'logged in':
            message = 'You are already logged in.'
        
        # Failed login
        elif message_type == 'login failed':
            message = 'Login failed.'
        
        # Other messages
        
        elif message_type == 'login successful':
            message = 'You have logged in successfully.'
        
        else:
            message = "Undefined response message."
        
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
        
        # MOTD changed
        elif message_type == 'motd':
            message = '{0} has updated MOTD to {1}.'.format(*args)
        
        # Flags changed
        elif message_type == 'flags':
            message = 'Flags have been updated to: {0}'.format(*args)
        
        # Muted
        elif message_type == 'part':
            message = '{0} has been muted by {1}.'.format(*args)
        
        # Force-killed
        elif message_type == 'killed':
            message = '{0} was just owned by {1}.'.format(*args)
        
        self.server.message_channel(channel, message)
