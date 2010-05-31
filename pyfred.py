#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import os.path

from bot import *
import parsers
from pokemon import Pokemon

HOST = 'localhost'
PORT = 8446
USERNAME = 'Fred'
PASSWORD = 'qwerty'
TEAM_DIR = "teams/"
TEAMS = ["team6.sbt", "team7.sbt", "team8.sbt", "team9.sbt", "team10.sbt"]
# An awesome, super human robot capable of beating any challenger
class PyFred(MessageHandler):
    
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
            
    def handle_incoming_challenge(self, user, generation, n):
        #too lazy to handle n > 1
        if (n > 1):
            self.reject_challenge(user)
        else:
            file = TEAM_DIR + TEAMS[random.randint(0, len(TEAMS) - 1)]
            file = os.path.normpath(file)
            team = parsers.parse_team_file(file)
            self.challenges[user] = file
            self.accept_challenge(user, team)
    
    def handle_battle_begin(self, fid, user, party):
        b = Battle(fid, self, party, user, self.challenges[user])
        self.battles[fid] = b
        del self.challenges[user]
    
    def handle_battle_use_move(self, fid, party, slot, name, id):
        self.battles[fid].handle_use_move(party, id)
        
    def handle_battle_send_out(self, fid, party, slot, index, name, id, gender, level):
        self.battles[fid].handle_send_out(party, index, id, gender, level)
        
    def handle_battle_health_change(self, fid, party, slot, delta, total, denominator):
        self.battles[fid].handle_health_change(party, delta, total, denominator)
        
    def handle_battle_fainted(self, fid, party, slot, name):
        self.battles[fid].handle_fainted(party)
        
    def handle_battle_print(self, fid, cat, id, args):
        self.battles[fid].print_message(cat, id, args)
        
    def handle_request_action(self, fid, slot, pos, replace, switches, can_switch, forced, moves):
        self.battles[fid].request_action(slot, pos, replace, switches, can_switch, forced, moves)
        
    def handle_battle_begin_turn(self, fid, turn):
        self.battles[fid].start_turn(turn)

        
    def handle_battle_victory(self, fid, party):
        battle = self.battles[fid]
        winner = (battle.party == party)
        battle.handle_victory(winner)
        del self.battles[fid]

    def handle_battle_set_move(self, fid, index, slot, id, pp, max):
        battle = self.battles[fid]
        battle.set_move(index, slot, id, pp, max)
       
##############################################################
class Battle:
    def __init__(self, fid, handler, party, opponent, team):
        self.fid = fid
        self.handler = handler
        self.party = party
        self.opponent = opponent
        self.teams = [[], []]
        self.teams[party] = parsers.parse_team_file(team)
        for i in range(6):
            self.teams[party - 1].append(Pokemon(moves=[]))
        self.active = [0, 0]
        
    # send a message to the users in this battle
    def send_message(self, msg):
        self.handler.send_message(self.fid, msg)
        
    def send_move(self, index, target):
        self.handler.send_move(self.fid, index, target)
        
    def send_switch(self, index):
        self.handler.send_switch(self.fid, index)
    
    def start_turn(self, turn):
        if turn == 1:
            self.send_message("Prepare to lose %s!" % self.opponent) 
        
    def print_message(self, cat, id, args):
        #print cat, id, args
        pass
    
    def handle_use_move(self, party, id):
        if party != self.party:
            p = self.teams[party][self.active[party]]
            move_list = self.handler.client.move_list
            move = None
            for name in move_list:
                if move_list[name]["id"] == id:
                    move = move_list[name]
                    break
            if not move in p.moves:
                p.moves.append(move)
    
    def handle_send_out(self, party, index, id, gender, level):
        self.active[party] = index
        p = self.teams[party][index]
        if p.pokemonspecies is None:
            species_list = self.handler.client.species_list
            if party is self.party:
                p.pokemonspecies = species_list[p.species]
            else:
                species = None
                for key in species_list:
                    if species_list[key]["id"] == id:  
                        species = species_list[key]
                        break
                p.pokemonspecies = species
    
    def handle_health_change(self, party, delta, total, denominator):
        self.teams[party][self.active[party]].health = (total, denominator)
        
    def handle_fainted(self, party):
        self.teams[party][self.active[party]].fainted = True
        
    def handle_victory(self, winner):
        if winner:
            self.send_message("I am a polymath")
            verb = "Won"
        else:
            self.send_message("You are a polymath")
            verb = "Lost"
        self.handler.leave_channel(self.fid)
        print verb, "a battle against", self.opponent
    
    def set_move(self, index, slot, id, pp, max):
        move_list = self.handler.client.move_list
        for name, move in move_list.items():
            if move["id"] == id:
                self.teams[party][index].moves[slot] = move
                break                
    
    def get_active(self, us):
        party = self.party if us else self.party - 1
        return self.teams[party][self.active[party]]
            
    def calc_max_threat(self, moves, our_types, their_types):
        max_threat = 0
        for t, power in moves:
            mult = get_effectiveness(t, our_types)
            threat = mult * power
            if t in their_types:
                threat *= 1.5
            max_threat = max(max_threat, threat)
        return max_threat
    
    def get_best_switch(self, available, opponent, comparison=99999):
        min_threat = 9999999
        min_index = -1
        for i in available:
            p = self.teams[self.party][i]
            if p.pokemonspecies is None:
                p.pokemonspecies = self.handler.client.species_list[p.species]
            moves = self.get_move_tuples(opponent)
            threat = self.calc_max_threat(moves, p.pokemonspecies["types"], opponent.pokemonspecies["types"])
            if threat < min_threat:
                min_threat = threat
                min_index = i
        if min_threat < comparison:
            return min_index
        else:
            return -1
    
    def get_move_tuples(self, p):
        moves = []
        for move in p.moves:
            move_type = move["type"]
            if move["class"] != "Other":
                moves.append((move_type, move["power"]))
        for t in p.pokemonspecies["types"]:
            # could be better but guess a 70 power move
            moves.append((t, 70))
        return moves
    
    def get_best_attack(self, attacker, defender):
        max_damage = 0
        max_index = -1
        for i, move in enumerate(attacker.moves):
            move = self.handler.client.move_list[move[0]]
            # stop from using dream eater and focus punch
            if (move["class"] == "Other") or (move["id"] in [144, 105]): continue
            type = move["type"]
            power = move["power"]
            damage = power * get_effectiveness(type, defender.pokemonspecies["types"])
            if type in attacker.pokemonspecies["types"]: damage *= 1.5
            if damage > max_damage:
                max_damage = damage
                max_index = i
        return max_index
            
    def request_action(self, slot, pos, replace, switches, can_switch, forced, moves):
        me = self.get_active(True)
        them = self.get_active(False)
        
        if forced:
            self.send_move(1, 1)
        else:
            available = []
            for i in range(len(switches)):
                if switches[i]:
                    available.append(i)
            if replace:
                #time.sleep(1.5)
                self.send_switch(self.get_best_switch(available, them))
            else:
                moves = []
                for move in them.moves:
                    move_type = move["type"]
                    if move["class"] != "Other":
                        moves.append((move_type, move["power"]))
                for t in them.pokemonspecies["types"]:
                    # could be better but guess a 70 power move
                    moves.append((t, 70))
                max_threat = self.calc_max_threat(moves, me.pokemonspecies["types"], them.pokemonspecies["types"])
                if max_threat > 180: switch = 0.95
                elif max_threat > 150: switch = 0.75
                elif max_threat > 120: switch = 0.4
                elif max_threat > 90: switch = 0.1
                else: switch = 0.05
                rand = random.random()
                best_switch = self.get_best_switch(available, them, max_threat)
                if can_switch and (rand < switch) and (best_switch >= 0):
                    self.send_switch(best_switch)
                else:
                    best_move = self.get_best_attack(me, them)
                    self.send_move(best_move, 1 - self.party)
    
##############################################################

TYPES = { "Normal" : 0, "Fire" : 1, "Water" : 2, "Electric" : 3, "Grass" : 4, "Ice" : 5, "Fighting" : 6, "Poison" : 7, 
    "Ground" : 8, "Flying" : 9, "Psychic" : 10, "Bug" : 11, "Rock" : 12, "Ghost" : 13, "Dragon" : 14, "Dark" : 15, 
    "Steel" : 16, "Typeless" : 17 }

EFFECTIVENESS = [   [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0, 1, 1, 0.5, 1 ],
	[ 1, 0.5, 0.5, 1, 2, 2, 1, 1, 1, 1, 1, 2, 0.5, 1, 0.5, 1, 2, 1 ],
	[ 1, 2, 0.5, 1, 0.5, 1, 1, 1, 2, 1, 1, 1, 2, 1, 0.5, 1, 1, 1 ],
	[ 1, 1, 2, 0.5, 0.5, 1, 1, 1, 0, 2, 1, 1, 1, 1, 0.5, 1, 1, 1 ],
	[ 1, 0.5, 2, 1, 0.5, 1, 1, 0.5, 2, 0.5, 1, 0.5, 2, 1, 0.5, 1, 0.5, 1 ],
	[ 1, 0.5, 0.5, 1, 2, 0.5, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 0.5, 1 ],
	[ 2, 1, 1, 1, 1, 2, 1, 0.5, 1, 0.5, 0.5, 0.5, 2, 0, 1, 2, 2, 1 ],
	[ 1, 1, 1, 1, 2, 1, 1, 0.5, 0.5, 1, 1, 1, 0.5, 0.5, 1, 1, 0, 1 ],
	[ 1, 2, 1, 2, 0.5, 1, 1, 2, 1, 0, 1, 0.5, 2, 1, 1, 1, 2, 1 ],
	[ 1, 1, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 0.5, 1 ],
	[ 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 0.5, 1, 1, 1, 1, 0, 0.5, 1 ],
	[ 1, 0.5, 1, 1, 2, 1, 0.5, 0.5, 1, 0.5, 2, 1, 1, 0.5, 1, 2, 0.5, 1 ],
	[ 1, 2, 1, 1, 1, 2, 0.5, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 0.5, 1 ],
	[ 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 0.5, 1 ],
	[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0.5, 1 ],
	[ 1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 0.5, 1 ],
	[ 1, 0.5, 0.5, 0.5, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0.5, 1 ],
    [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ]
]

def get_effectiveness(type1, type2):
    mult = 1
    for t in type2:
        mult *= EFFECTIVENESS[TYPES[type1]][TYPES[t]]
    return mult

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
    client.set_handler(PyFred())
    client.authenticate(USERNAME, PASSWORD)
    client.run()