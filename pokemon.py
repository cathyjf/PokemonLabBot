#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# File:   pokemon.py              
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

class Pokemon:
    def __init__(self, species=-1, nickname="", happiness=255, level=100, gender="Male", 
                        nature="", item="", ability="", moves=[], stats=[]):
        self.species = species
        self.nickname = nickname
        self.happiness = happiness
        self.level = level
        self.gender = gender
        self.nature = nature
        self.item = item
        self.ability = ability
        self.moves = moves
        self.stats = stats
        self.health = (1, 1)
        self.fainted = False
        self.pokemonspecies = None
    
    def get_species(self):
        return self.species
    
    def get_nickname(self):
        return self.nickname
    
    def get_happiness(self):
        return self.happiness
    
    def get_level(self):
        return self.level
    
    def get_gender(self):
        values = {
            "Male"   : 1,
            "Female" : 2,
            "None"   : 0
        }
        return values[self.gender]
    
    def get_nature(self):
        values = {
            "Lonely" : 1, "Brave" : 2, "Adamant" : 3, "Naughty" : 4, "Bold" : 5, "Relaxed" : 7,
            "Impish" : 8, "Lax" : 9, "Timid" : 10, "Hasty" : 11, "Jolly" : 13, "Naive" : 14, "Modest" : 15,
            "Mild" : 16, "Quiet" : 17, "Rash" : 19, "Calm" : 20, "Gentle" : 21, "Sassy" : 22, "Careful" : 23,
            "Quirky" : 24, "Hardy" : 0, "Serious" : 12, "Bashful" : 18, "Docile" : 6
        }
        return values[self.nature]
    
    def get_item(self):
        return self.item
        
    def get_ability(self):
        return self.ability
    
    def get_moves(self):
        return self.moves
        
    def get_stat(self, stat):
        return (self.stats[stat])
        
    def __repr__(self):
        things = [self.species, self.nickname, self.happiness, self.level, self.gender, self.nature,
                    self.item, self.ability, self.moves, self.stats]
        return "\n".join([str(i) for i in things])
    
