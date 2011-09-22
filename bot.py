#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# File:   bot.py              
#
# This file is a part of Shoddy Battle.
# Copyright (C) 2011  Catherine Fitzpatrick and Benjamin Gwin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, visit the Free Software Foundation, Inc.
# online at http://gnu.org.
#
##############################################################################

import socket
import hashlib
import array
import threading
import Queue
import time
from struct import *
from array import array

from aes import AES
import parsers

################################################################################

# A message received from the server.
class InMessage:
    # data - an array of unsigned bytes (i.e. array('B'))
    def __init__(self, data):
        self.buffer = data

    def read_byte(self):
        return self.buffer.pop(0)

    def read_short(self):
        data0 = self.read_byte()
        data1 = self.read_byte()
        return unpack('>h', pack('BB', data0, data1))[0]

    def read_unsigned_short(self):
        data0 = self.read_byte()
        data1 = self.read_byte()
        return unpack('>H', pack('BB', data0, data1))[0]

    def read_int(self):
        data0 = self.read_byte()
        data1 = self.read_byte()
        data2 = self.read_byte()
        data3 = self.read_byte()
        return unpack('>i', pack('BBBB', data0, data1, data2, data3))[0]

    def read_string(self):
        length = self.read_unsigned_short()
        ret = ''
        for i in range(length):
            ret += pack('B', self.read_byte())
        return ret

################################################################################

# A message that will be sent to the server.
class OutMessage:
    def __init__(self, code):
        self.buffer = array('B') # byte array
        self.buffer.append(code)

    def write_byte(self, _byte):
        self.buffer.append(_byte)
    
    def write_int(self, _int):
        self.buffer.fromstring(pack('>i', _int))

    def write_string(self, str):
        str = unicode(str)
        self.buffer.fromstring(pack('>H', len(str)))
        self.buffer.fromstring(str)

    def finalise(self):
        # note: we reverse the byte order when inserting the data into the buffer
        length = len(self.buffer) - 1
        insert = array('B', pack('<i', length)).tolist()
        for i in range(4):
            self.buffer.insert(1, insert[i])

    def to_string(self):
        return self.buffer.tostring()

    def __len__(self):
        return len(self.buffer)

    def __str__(self):
        return repr(self.buffer.tolist())

################################################################################

class BotClient:
    def __init__(self, host, port):
        self.socket = socket.socket()
        self.socket.connect((host, port))
        self.species_list = dict()
        self.move_list = dict()
        self.running = True
        self.send_queue = Queue.Queue()
        # proxy thread for sending messages
        thread = threading.Thread(target=BotClient.send_proxy, args=(self,))
        thread.daemon = True
        thread.start()
        # proxy thread for informing the server that we are still alive
        thread = threading.Thread(target=BotClient.activity_proxy, args=(self,))
        thread.daemon = True
        thread.start()

    def activity_proxy(self):
        while True:
            time.sleep(45)
            self.send(OutMessage(18)) # CLIENT_ACTIVITY

    def send_proxy(self):
        while True:
            msg = self.send_queue.get()
            msg.finalise()
            self.socket.sendall(msg.to_string())

    # send a message
    def send(self, msg):
        self.send_queue.put(msg)
    
    # initialises the species list from a species.xml file
    def init_species(self, file):
        #print "Initializing species list..."
        self.species_list = parsers.parse_species_list(file)
    
    # initialises the move list from a moves.xml file    
    def init_moves(self, file):
        #print "Initializing move list..."
        self.move_list = parsers.parse_move_list(file)
    
    # sets the handler that will respond to all messages received
    def set_handler(self, handler):
        self.handler = handler
        handler.client = self

    # attempt to register with the server
    def register(self, user, password):
        msg = OutMessage(2) # register account
        msg.write_string(user)
        msg.write_string(password)
        self.send(msg)

    # attempt to authenticate with the server
    def authenticate(self, user, password):
        self.user = user
        self.password = password
        msg = OutMessage(0) # request challenge
        msg.write_string(user)
        self.send(msg)

    # calculate the secret for the challenge-response exchange
    @staticmethod
    def get_shared_secret(password, secret_style, salt):
        if secret_style == 0:
            return password
        elif secret_style == 1:
            return hashlib.md5(password).hexdigest()
        elif secret_style == 2:
            return hashlib.md5(hashlib.md5(password).hexdigest() + salt).hexdigest()
        raise RuntimeError("Unknown secret_style of %i" % secret_style)

    # calculate the response to a challenge
    def get_challenge_response(self, challenge, secret_style, salt):
        m = hashlib.sha256()
        m.update(BotClient.get_shared_secret(self.password, secret_style, salt))
        digest = m.digest()
        key = [digest[0:16], digest[16:32]]
        for i in range(2):
            key[i] = array('B', key[i]).tolist()
        aes = AES()
        challenge = aes.decrypt(challenge, key[1], 16)
        challenge = aes.decrypt(challenge, key[0], 16)
        r = unpack('>i', pack('BBBB', challenge[0], challenge[1], challenge[2], challenge[3]))[0] + 1
        response = array('B', pack('>i', r)).tolist()
        while len(response) < 16:
            response.append(0)
        response = aes.encrypt(response, key[0], 16)
        response = aes.encrypt(response, key[1], 16)
        return response

    # read exactly the specified number of bytes from the server and return the
    # result in the form of an InMessage
    def recvfully(self, bytes):
        data = array('B')
        read = 0
        while read < bytes:
            str = self.socket.recv(bytes - read)
            if str == "": raise IOError
            read += len(str)
            data.fromstring(str)
        return InMessage(data)

    # run the bot client
    def run(self):
        while True:
            try:
                # read in the five byte header
                msg = self.recvfully(5)
                # extract the message type and length components
                code = msg.read_byte()
                length = msg.read_int()
                # read in the whole message
                msg = self.recvfully(length)
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                print "Disconnected from server"
                break
            # call the handler, if any, for the message
            self.handle_message(code, msg)
    
    def handle_message(self, code, msg):
        if code == 1:
            # PASSWORD_CHALLENGE
            handle_challenge(self, msg)
        elif code == 0:
            # WELCOME_MESSAGE
            # int32  : server version
            # string : server name
            # string : welcome message
            self.handler.handle_welcome_message(msg.read_int(), msg.read_string(), msg.read_string())
        elif code == 2:
            # REGISTRY_RESPONSE
            # byte   : type
            # string : details
            self.handler.handle_registry_response(msg.read_byte(), msg.read_string())
        elif code == 4:
            # CHANNEL_INFO
            # _int 32 : channel id
            # byte   : channel info
            # string : channel name
            # string : channel topic
            # int32  : channel flags
            # int32  : number of users
            # for each user:
            #   string : name
            #   int32  : flags
            id, info, name = msg.read_int(), msg.read_byte(), msg.read_string()
            topic, flags, pop = msg.read_string(), msg.read_int(), msg.read_int()
            users = [(msg.read_string(), msg.read_int()) for i in range(pop)]
            self.handler.handle_channel_info(id, info, name, topic, flags, users)
        elif code == 5:
            # CHANNEL_JOIN_PART
            # int32  : channel id
            # string : user
            # byte   : joining?
            self.handler.handle_channel_join_part(msg.read_int(), msg.read_string(), msg.read_byte())
        elif code == 6:
            # CHANNEL_STATUS
            # int32  : channel id
            # string: invoker
            # string : user
            # int32  : flags
            self.handler.handle_channel_status(msg.read_int(), msg.read_string(), msg.read_string(), msg.read_int())
        elif code == 7:
            # CHANNEL_LIST
            # int32 : number of channels
            # for each channel:
            #   string : name
            #   byte   : type
            #   string : topic
            #   int32 : population
            n = msg.read_int()
            channels = [(msg.read_string(), msg.read_byte(), msg.read_string(), msg.read_int()) for i in range(n)]
            self.handler.handle_channel_list(channels)
        elif code == 8:
            # CHANNEL_MESSAGE
            # int32  : channel id
            # string : user
            # string : message
            self.handler.handle_channel_message(msg.read_int(), msg.read_string(), msg.read_string())
        elif code == 9:
            # INCOMING_CHALLENGE
            # string : user
            # byte   : generation
            # int32  : active party size
            # int32  : max team length
            self.handler.handle_incoming_challenge(msg.read_string(), msg.read_byte(), msg.read_int(), msg.read_int())
        elif code == 10:
            # FINALISE_CHALLENGE
            # string : user
            # byte   : whether the challenge was accepted
            self.handler.handle_finalise_challenge(msg.read_string(), msg.read_byte())
        elif code == 12:
            # BATTLE_BEGIN
            # int32  : field id
            # string : opponent
            # byte   : party
            self.handler.handle_battle_begin(msg.read_int(), msg.read_string(), msg.read_byte())
        elif code == 13:
            # REQUEST_ACTION
            # int32  : field id
            # byte   : slot of pokemon
            # byte   : position of pokemon
            # byte   : whether this is a replacement
            # byte   : index of the request sequence
            # byte   : number of sequential requests
            # int32  : number of pokemon
            # for each pokemon
            #     byte: whether it is legal to switch to this pokemon
            # if not replacement
            #     byte : whether switching is legal
            #     byte : whether there is a forced move
            #     if not forced:
            #         int32 : total number of moves
            #         for each move:
            #             byte: whether the move is legal
            fid, slot, pos, replace = msg.read_int(), msg.read_byte(), msg.read_byte(), msg.read_byte()
            request_sequences = msg.read_byte()
            sequential_requests = msg.read_byte()
            num_pokes = msg.read_int()
            switches = [msg.read_byte() for i in range(num_pokes)]
            can_switch = forced = False
            moves = []
            if replace == 0:
                can_switch = msg.read_byte()
                forced = msg.read_byte()
                if forced == 0:
                    num_moves = msg.read_int()
                    moves = [msg.read_byte() for i in range(num_moves)]
            if not 1 in switches:
                can_switch = False
            self.handler.handle_request_action(fid, slot, pos, replace, switches, can_switch, forced, moves)
        elif code == 14:
            # BATTLE_POKEMON
            # int32 : field id
            # for 0..1:
            #     for 0..n-1:
            #         int16 : species id
            #         if id != -1:
            #             byte: gender
            #             byte: level
            #             byte: shiny
            
            # the bot probably doesn't need to care about this
            pass
        elif code == 15:
            # BATTLE_PRINT
            # int32 : field id
            # byte  : category
            # int16 : message id
            # byte  : number of arguments
            # for each argument:
            #   string : value of the argument
            fid, cat, id = msg.read_int(), msg.read_byte(), msg.read_short()
            argc = msg.read_byte()
            args = [msg.read_string() for i in range(argc)]
            self.handler.handle_battle_print(fid, cat, id, args)
        elif code == 16:
            # BATTLE_VICTORY
            # int32 : field id
            # int16 : party id
            self.handler.handle_battle_victory(msg.read_int(), msg.read_short())
        elif code == 17:
            # BATTLE_USE_MOVE
            # int32  : field id
            # byte   : party
            # byte   : slot
            # string : user [nick]name
            # int16  : move id
            self.handler.handle_battle_use_move(msg.read_int(), msg.read_byte(),
                                                msg.read_byte(), msg.read_string(), msg.read_short())
        elif code == 18:
            # BATTLE_WITHDRAW
            # int32  : field id
            # byte   : party
            # byte   : slot
            # string : user [nick]name
            self.handler.handle_battle_withdraw(msg.read_int(), msg.read_byte(), msg.read_byte(), msg.read_string())
        elif code == 19:
            # BATTLE_SEND_OUT
            # int32  : field id
            # byte   : party
            # byte   : slot
            # byte   : index
            # string : user [nick]name
            # int16  : species id
            # byte   : gender
            # byte   : level
            self.handler.handle_battle_send_out(msg.read_int(), msg.read_byte(), msg.read_byte(), msg.read_byte(),
                                            msg.read_string(), msg.read_short(), msg.read_byte(), msg.read_byte())
        elif code == 20:
            # BATTLE_HEALTH_CHANGE
            # int32 : field id
            # byte  : party
            # byte  : slot
            # int16 : delta health in [0, 48]
            # int16 : new total health in [0, 48]
            # int16 : denominator
            self.handler.handle_battle_health_change(msg.read_int(), msg.read_byte(), msg.read_byte(),
                                                    msg.read_short(), msg.read_short(), msg.read_short())
        elif code == 21:
            # BATTLE_SET_PP
            # int32 : field id
            # byte  : party
            # byte  : slot
            # byte  : pp
            self.handler.handle_battle_set_pp(msg.read_int(), msg.read_byte(), msg.read_byte(), msg.read_byte())
        elif code == 22:
            # BATTLE_FAINTED
            # int32  : field id
            # byte   : party
            # byte   : slot
            # string : user [nick]name
            self.handler.handle_battle_fainted(msg.read_int(), msg.read_byte(), msg.read_byte(), msg.read_string())
        elif code == 23:
            # BATTLE_BEGIN_TURN
            # int32 : field id
            # int16 : turn count
            self.handler.handle_battle_begin_turn(msg.read_int(), msg.read_short())
        elif code == 24:
            #SPECTATOR_BEGIN
            pass
        elif code == 25:
            # BATTLE_SET_MOVE
            # int32  : field id
            # byte   : pokemon
            # byte   : move slot
            # int16  : new move
            # byte   : pp
            # byte   : max pp
            self.handler.handle_battle_set_move(msg.read_int(), msg.read_byte(), msg.read_byte(), msg.read_short(), 
                msg.read_byte(), msg.read_byte())
        elif code == 26:
            # METAGAME_LIST
            # int16  : metagame count
            # for 0..metagame count - 1:
            #    byte   : index
            #    string : name
            #    string : id
            #    string : description
            #    byte   : party size
            #    byte   : max team length
            #    int16  : ban list count
            #    for 0..ban list count - 1:
            #        int16  : species id
            #    int16  : clause count
            #    for 0..clause count - 1:
            #        string : clause name
            #    byte    : if timing is enabled
            #    if timing is enabled:
            #       short : pool length
            #       byte  : periods
            #       short : period length
            mcount = msg.read_short()
            metagames = []
            for i in xrange(0, mcount):
                index, name, id, desc = msg.read_byte(), msg.read_string(), msg.read_string(), msg.read_string()
                party_size, max_team_length = msg.read_byte(), msg.read_byte()
                bans = [msg.read_short() for i in xrange(0, msg.read_short())]
                clauses = [msg.read_string() for i in xrange(0, msg.read_short())]
                timing = (msg.read_byte() != 0)
                if timing:
                    pool, periods, period_length = msg.read_short(), msg.read_byte(), msg.read_short()
                else:
                    pool = periods = period_length = -1
                metagames.append((index, name, id, desc, party_size, max_team_length, bans, clauses, pool, periods, period_length))
            self.handler.handle_metagame_list(metagames)
        else:
            pass #print "Unknown code: ", code

# respond to a password challenge
def handle_challenge(client, msg):
    challenge = []
    for i in range(16):
        challenge.append(msg.read_byte())
    secret_style = msg.read_byte()
    salt = msg.read_string()
    response = client.get_challenge_response(challenge, secret_style, salt)
    out = OutMessage(1)
    for i in range(16):
        out.write_byte(response[i])
    client.send(out)

################################################################################
# A class that handles messages from the server
# Subclass this to create your own bot
class MessageHandler:
    
    # Sends a message to a certain channel
    def send_message(self, channel, message):
        msg = OutMessage(4)
        msg.write_int(channel)
        msg.write_string(message)
        self.client.send(msg)
        
    # join a channel
    def join_channel(self, channel):
        msg = OutMessage(3)
        msg.write_string(channel)
        self.client.send(msg)
    
    # leave a channel
    def leave_channel(self, channel):
        msg = OutMessage(11)
        msg.write_int(channel)
        self.client.send(msg)
    
    # send a challenge to a user using the given team
    def send_challenge(self, options):
        msg = OutMessage(6)
        msg.write_string(options['target'])
        msg.write_byte(options.get('generation', 1))
        msg.write_int(options.get('n', 1))
        msg.write_int(options.get('team_length', 6))
        metagame = options.get('metagame', 0)
        msg.write_int(metagame)
        if metagame != -1:
            # TODO: actually handle this
            pass
        self.client.send(msg)
            
    # accept a challenge with a user, using the given team
    def accept_challenge(self, user, team):
        msg = OutMessage(7)
        msg.write_string(user)
        msg.write_byte(1)
        self.write_team(msg, team)
        self.client.send(msg)
    
    # reject an incoming challenge from the given user    
    def reject_challenge(self, user):
        msg = OutMessage(7)
        msg.write_string(user)
        msg.write_byte(0)
        self.client.send(msg)
    
    # sends a team to the server
    def finalise_challenge(self, user, team):
        msg = OutMessage(8)
        msg.write_string(user)
        self.write_team(msg, team)
        self.client.send(msg)
        
    # writes a list of Pokemon objects to a message    
    def write_team(self, msg, team):
        msg.write_int(len(team))
        for p in team:
            msg.write_int(self.client.species_list[p.get_species()]["id"])
            msg.write_string(p.get_nickname())
            msg.write_byte(0)
            msg.write_byte(p.get_gender())
            msg.write_byte(p.get_happiness())
            msg.write_int(p.get_level())
            msg.write_string(p.get_item())
            msg.write_string(p.get_ability())
            msg.write_int(p.get_nature())
            moves = p.get_moves()
            msg.write_int(len(moves))
            for move in moves:
                msg.write_int(self.client.move_list[move[0]]["id"])
                msg.write_int(move[1])
            for stat in ["HP", "Atk", "Def", "Spd", "SpAtk", "SpDef"]:
                tup = p.get_stat(stat)
                msg.write_int(tup[0])
                msg.write_int(tup[1])
    
    # sends a move selection for the specified battle, using moves[index]
    # and targeting "target"      
    def send_move(self, fid, index, target = 1):
        msg = OutMessage(10)
        msg.write_int(fid)
        msg.write_byte(0)
        msg.write_byte(index)
        msg.write_byte(target)
        #msg.write_byte(1)
        self.client.send(msg)
    
    # switch to pokekmon[index] on the specified battle 
    def send_switch(self, fid, index):
        msg = OutMessage(10)
        msg.write_int(fid)
        msg.write_byte(1)
        msg.write_byte(index)
        msg.write_byte(0)
        self.client.send(msg)
    
    # Welcome message sent when connecting to a server
    # version: int - the server version
    # name: string - the name of the server
    # message: string - the welcome message
    def handle_welcome_message(self, version, name, message):
        pass
        
    # Response sent after an attempted authentication
    # type: int - the message code
    #     Notable values:
    #         4 - nonexistent account
    #         5 - failed challenge (wrong password)
    #         6 - Banned
    #         7 - Success!
    # details: string - an additional string providing details about the response.
    #                   Only present for banned message (at the moment)
    def handle_registry_response(self, type, details):
        pass
        
    # Information sent about a channel after it has been joined
    # id: int - the id of this channel
    # info: int - the type of this channel, i.e. 0 for normal, 1 for battle
    # name: string - the name of this channel
    # topic: string - the current topic in this channel
    # users: list of tuples of the form (name, flags) - the users in this channel
    def handle_channel_info(self, id, info, name, topic, flags, users):
        pass
        
    # Sent when a user joins or leaves a channel
    # id: int - the id of the channel
    # user: string - the name of the user
    # joining: bool - if the user is joining
    def handle_channel_join_part(self, id, user, joining):
        pass
        
    # Sent when a mode is changed
    # id: int - the id of the channel
    # invoker: string - the person who changed the status
    # user: string - the name of the user
    # flags: int - the new flags for the user
    def handle_channel_status(self, id, invoker, user, flags):
        pass
        
    # List of channels sent when joining a server
    # channels: list of tuples of the form (name, type, topic, population) 
    #               - similar paramaters to handle_channel_info
    def handle_channel_list(self, channels):
        pass
        
    # A text message sent in a channel
    # id: int - the id of the channel
    # user: string - the name of the user who sent the message
    # msg: string - the body of the message
    def handle_channel_message(self, id, user, msg):
        pass
        
    # Incoming challenge sent by another player
    # user: string - the name of the challenger
    # generation: int - the id of the generation
    # n: int - the number of pokemon for each side e.g. 2 for 2 v. 2
    # team_length - the maximum team length for this challenge
    # ...clauses...
    def handle_incoming_challenge(self, user, generation, n, team_length):
        pass
        
    # Sent when an opponent accepts/rejects your challenge
    # user: string - the name of the user
    # accepted: bool - whether the challenge was accepted 
    def handle_finalise_challenge(self, user, accepted):
        pass
    
    # Sent when a battle begins
    # fid: int - the unique id of the battle
    # user: string - your opponent
    # party: int - which party you are - either 0 or 1
    def handle_battle_begin(self, fid, user, party):
        pass
    
    # Sent when you are prompted to move/switch
    # slot: int - the index of the pokemon within your active pokemon
    # pos: int - the position of the pokemon within your party
    # replace: bool - if you need to select a replacement
    # switches: list of bools - whether you are able to switch to certain pokemon
    # canSwitch: bool - if you are permitted to switch
    # forced: bool - if you have a forced move
    # moves: list of bools - whether you may select a certain move
    def handle_request_action(self, fid, slot, pos, replace, switches, can_switch, forced, moves):
        pass
    
    # Used to send most messages in the battle such as "Slaking is loafing around!"
    # These messages need a .lang file to fetch the desired string
    # cat: int - the category index within the .lang file
    # id: int - the id of the string within the cateogry
    # args: list of strings - arguments to be substituted _into the string
    def handle_battle_print(self, fid, cat, id, args):
        pass
    
    # Sent when one party is victorious in a battle
    # party: int - the party id that won (0 or 1)   
    def handle_battle_victory(self, fid, party):
        pass
    
    # Sent when a pokemon uses a move
    # party: int - the index of the party (0 or 1)
    # name: string - the [nick]name of the pokemon that used the move
    # id: int - the id of the move (see moves.xml)   
    def handle_battle_use_move(self, fid, party, slot, name, id):
        pass
    
    # Sent when a trainer withdraws a pokemon
    # Arguments similar to handleBattleUseMove
    def handle_battle_withdraw(self, fid, party, slot, name):
        pass
    
    # Sent when a trainer sends out a pokemon
    # index: int - the index of the pokemon within the party
    # gender: int - 0 => none, 1 => male, 2 => female
    # level: int - the level of the pokemon
    def handle_battle_send_out(self, fid, party, slot, index, name, id, gender, level):
        pass
    
    # Sent when a health change occurs
    # delta: int - the change in health
    # total: int - the new health
    # denominator: int - the denominator to be used when expressing change    
    def handle_battle_health_change(self, fid, party, slot, delta, total, denominator):
        pass
    
    # Used to update the PP for a move
    # pokemon: int - the index of the pokemon within your team
    # move: int - the index of the move on that pokemon
    # pp: int - the new pp
    def handle_battle_set_pp(self, fid, pokemon, move, pp):
        pass
    
    # Sent when a pokemon is fainted
    # arguments same as handle_battle_use_move or handle_battle_withdraw
    def handle_battle_fainted(self, fid, party, slot, name):
        pass
    
    # Sent when a new turn begins
    # turn: int - the turn number    
    def handle_battle_begin_turn(self, fid, turn):
        pass
    
    # Changes one of a pokemon's moves e.g. for mimic
    # index: int - the index of the pokemon in your party
    # moveSlot: int - the slot to replace
    # moveId: int - the id of the new move
    # pp: int - the current pp of the move
    # maxPp: int - the maximum pp of the move
    def handle_battle_set_move(self, fid, index, move_slot, move_id, pp, max_pp):
        pass
    
    # A list of metagames sent from the server 
    # metagames: tuples of the form (index, name, id, description, party size, 
    #                                       max team length, ban list, clauses)
    # index: int - index of the metagame
    # name: string - formal name of the ladder
    # id: string - internal name of the ladder
    # description: string - a brief description of the ladder
    # party size: int - the number of active pokemon on each team
    # max team length: int - the maximum number of pokemon in a team
    # banlist: list of species ids for all banned pokemon
    # clauses: list of strings for the named clauses
    def handle_metagame_list(self, metagames):
        pass
