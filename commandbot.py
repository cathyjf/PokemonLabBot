#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# File:   commandbot.py              
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

from bot import *

HOST = 'localhost'
PORT = 8446

USERNAME = 'test2'
PASSWORD = 'test'

# A simple bot that can respond to user commands
class CommandBot(MessageHandler):
    
    def __init__(self):
        self.handlers = dict()
        self.add_handler("echo", self.echo)
        self.add_handler("polymath", self.polymath)
    
    # register a handler that will perform "func"
    # when "!command" is said
    def add_handler(self, command, func):
        self.handlers[command] = func
    
    def handle_welcome_message(self, version, name, message):
        print name
        print message
        
    def handle_registry_response(self, type, details):
        if type == 7:
            print "Successfully authenticated"
            self.join_channel("main")
        else:
            print "Authentication failed, code ", type
            if details: print details
    
    def handle_channel_info(self, id, type, name, opic, flags, users):
        if name == "main":
            self.main = id
        
    # if the message starts with !, try to parse the command
    def handle_channel_message(self, id, user, msg):
        if msg[0] == "!":
            msg = msg[1:]
            parts = msg.split(" ")
            command = parts[0]
            if len(parts) > 1:
                args = parts[1:]
            else:
                args = []
            if command in self.handlers:
                self.handlers[command](id, user, args)
    
    
    # reject all incoming challenges
    def handle_incoming_challenge(self, user, generation, n):
        self.reject_challenge(user)
        
    # simple example - echo back the user's message
    def echo(self, id, user, args):
        self.send_message(id, " ".join(args))
    
        # speaks the truth    
    def polymath(self, id, user, args):
        if len(args) > 0:
            user = " ".join(args)
        if user.lower().find("colin") != -1:
            self.send_message(id, "{0} is not a polymath".format(user))
        else:
            self.send_message(id, "{0} is a polymath".format(user))
        
##############################################################
if __name__ == "__main__":
    try:
        client = BotClient(HOST, PORT)
    except socket.error:
        print "Failed to connect to host {0} on port {1}".format(HOST, PORT)
        exit(1)
    client.set_handler(CommandBot())
    client.authenticate(USERNAME, PASSWORD)
    client.run()
