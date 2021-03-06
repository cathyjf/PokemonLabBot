#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# File:   idlebot.py              
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

import random
import time
import os.path

from bot import *
import parsers
from pokemon import Pokemon

HOST = 'localhost'
PORT = 8446
USERNAME = 'idlebot'
PASSWORD = 'test'
TEAM_DIR = "teams/"
TEAMS = ["team6.sbt"]

class IdleBot(MessageHandler):
    
    def __init__(self):
        self.battles = dict()
        self.challenges = dict()
        random.seed()
    
    def handle_welcome_message(self, version, name, message):
        print name
        print message
    
    def handle_metagame_list(self, metagames):
        self.metagames = metagames
        
    def handle_registry_response(self, type, details):
        if type == 7:
            print "Successfully authenticated"
            self.join_channel("main")
        else:
            print "Authentication failed, code ", type
            if details: print details
            
    def handle_incoming_challenge(self, user, generation, n, team_length):
        file = TEAM_DIR + TEAMS[random.randint(0, len(TEAMS) - 1)]
        file = os.path.normpath(file)
        team = parsers.parse_team_file(file)
        self.challenges[user] = file
        self.accept_challenge(user, team)

##############################################################
if __name__ == "__main__":
    try:
        client = BotClient(HOST, PORT)
    except socket.error:
        print "Failed to connect to host {0} on port {1}".format(HOST, PORT)
        exit(1)
    t1 = time.time()
    client.init_species("species.xml")
    t2 = time.time()
    client.init_moves("moves.xml")
    t3 = time.time()
    print "Loaded species in", (t2-t1)*1000, "milliseconds"
    print "Loaded moves in", (t3-t2)*1000, "milliseconds"
    client.set_handler(IdleBot())
    client.authenticate(USERNAME, PASSWORD)
    client.run()
