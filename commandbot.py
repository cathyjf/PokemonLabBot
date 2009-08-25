#!/usr/bin/env python
# -*- coding: utf-8 -*-

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