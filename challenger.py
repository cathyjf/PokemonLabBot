#!/usr/bin/python
from bot import *
from pyfred import *
from parser import *

OPPONENT = 'idlebot'
USERNAME = 'test'
PASSWORD = 'test'

class Challenger(PyFred):
    def challenge(self):
        file = os.path.normpath("teams/team6.sbt")
        self.challenges[OPPONENT] = file
        self.send_challenge({ 'target' : OPPONENT })
        
    def handle_registry_response(self, type, details):
        if type == 7:
            print "authenticated"
            self.join_channel("main")
            self.challenge()
            
    def handle_finalise_challenge(self, user, accepted):
        if accepted:
            file = os.path.normpath("teams/team6.sbt")
            team = parsers.parse_team_file(file)
            self.finalise_challenge(user, team)
    
    def handle_battle_victory(self, fid, party):
        self.challenge()
        
if __name__ == '__main__':
	client = BotClient('localhost', 8446)
	client.init_species("species.xml")
	client.init_moves("moves.xml")
	client.set_handler(Challenger())
	client.authenticate(USERNAME, PASSWORD)
	client.run()
