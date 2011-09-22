#!/usr/bin/python
##############################################################################
#
# File:   challenger.py              
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
from pyfred import *
from parser import *
import sys

OPPONENT = 'Fred'

class Challenger(PyFred):
    def __init__(self, username):
        PyFred.__init__(self)
        self.username = username

    def challenge(self):
        file = os.path.normpath("teams/team10.sbt")
        self.challenges[OPPONENT] = file
        self.send_challenge({ 'target' : OPPONENT })
        
    def handle_registry_response(self, type, details):
        if type == 7: # SUCCESSFUL_LOGIN
            #print "authenticated"
            self.join_channel("main")
            self.challenge()
        elif type == 8: # USER_ALREADY_ON
            print("USER_ALREADY_ON: %s" % self.username)
            
    def handle_finalise_challenge(self, user, accepted):
        if accepted:
            file = os.path.normpath("teams/team10.sbt")
            team = parsers.parse_team_file(file)
            self.finalise_challenge(user, team)
    
    def handle_battle_victory(self, fid, party):
        self.challenge()

def start_challenger(server, port, username, password):
    client = BotClient(server, port)
    client.init_species("species.xml")
    client.init_moves("moves.xml")
    client.set_handler(Challenger(username))
    client.register(username, password)
    client.authenticate(username, password)
    client.run()

if __name__ == '__main__':
    start_challenger('localhost', 9000, 'test', 'test')


