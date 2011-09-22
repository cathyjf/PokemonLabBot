#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# File:   parsers.py
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

try:
    import xml.etree.cElementTree as et
except:
    import xml.etree.ElementTree as et
import pokemon

def parse_team_file(file):
    tree = et.parse(file)
    team = []
    for p in tree.findall("pokemon"):
        species = p.get("species")
        nickname = p.findtext("nickname")
        try:
            happiness = int(p.findtext("happiness"))
        except:
            happiness = 255
        level = int(p.findtext("level"))
        gender = p.findtext("gender")
        nature = p.findtext("nature")
        item = p.findtext("item")
        ability = p.findtext("ability")
        moves = []
        for move in p.findall("moveset/move"):
            pp = int(move.get("pp-up"))
            name = move.text
            moves.append((name, pp))
        stats = {}
        for stat in p.findall("stats/stat"):
            name = stat.get("name")
            iv = int(stat.get("iv"))
            ev = int(stat.get("ev"))
            stats[name] = (iv, ev)
        poke = pokemon.Pokemon(species, nickname, happiness, level, gender, nature, item, ability, moves, stats)
        team.append(poke)
    return team

def parse_species_list(file):
    tree = et.parse(file)
    species = dict()
    for s in tree.findall("species"):
        name = s.get("name")
        temp = dict()
        temp["id"] = int(s.get("id"))
        types = []
        for elem in s.findall("type"):
            types.append(elem.text)
        temp["types"] = types
        bases = []
        for elem in s.findall("stats/base"):
            bases.append(int(elem.text))
        temp["bases"] = bases
        abilities = []
        for elem in s.findall("abilities/ability"):
            abilities.append(elem.text)
        temp["abilities"] = abilities
        species[name] = temp
    return species

def parse_move_list(file):
    tree = et.parse(file)
    moves = dict()
    for m in tree.findall("move"):
        move = dict()
        name = m.get("name")
        move["id"] = int(m.get("id"))
        move["type"] = m.findtext("type")
        move["class"] = m.findtext("class")
        move["power"] = int(m.findtext("power"))
        move["target"] = m.findtext("target")
        moves[name] = move
    return moves
