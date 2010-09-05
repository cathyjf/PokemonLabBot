#!/usr/bin/python
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
    start_challenger('localhost', 8446, 'test', 'test')


