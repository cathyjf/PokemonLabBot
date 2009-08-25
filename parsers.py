#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.dom.minidom
import pokemon

# extracts the text from a dom node
def get_text(parent):
    ret = ""
    for node in parent.childNodes:
        if node.nodeType == node.TEXT_NODE:
            ret += node.data
    return ret

def parse_team_file(file):
    dom = xml.dom.minidom.parse(file)
    team = []
    for p in dom.getElementsByTagName("pokemon"):
        species = p.getAttribute("species")
        nickname = get_text(p.getElementsByTagName("nickname")[0])
        level = int(get_text(p.getElementsByTagName("level")[0]))
        gender = get_text(p.getElementsByTagName("gender")[0])
        nature = get_text(p.getElementsByTagName("nature")[0])
        item = get_text(p.getElementsByTagName("item")[0])
        ability = get_text(p.getElementsByTagName("ability")[0])
        moves = []
        for move in p.getElementsByTagName("move"):
            pp = int(move.getAttribute("pp-up"))
            name = get_text(move)
            moves.append((name, pp))
        stats = {}
        for stat in p.getElementsByTagName("stat"):
            name = stat.getAttribute("name")
            iv = int(stat.getAttribute("iv"))
            ev = int(stat.getAttribute("ev"))
            stats[name] = (iv, ev)
        poke = pokemon.Pokemon(species, nickname, level, gender, nature, item, ability, moves, stats)
        team.append(poke)
    return team

def parse_species_list(file):
    dom = xml.dom.minidom.parse(file)
    species = dict()
    for s in dom.getElementsByTagName("species"):
        name = s.getAttribute("name")
        temp = dict()
        temp["id"] = int(s.getAttribute("id"))
        types = []
        for elem in s.getElementsByTagName("type"):
            types.append(get_text(elem))
        temp["types"] = types
        bases = []
        for elem in s.getElementsByTagName("base"):
            bases.append(int(get_text(elem)))
        temp["bases"] = bases
        abilities = []
        for elem in s.getElementsByTagName("ability"):
            abilities.append(get_text(elem))
        temp["abilities"] = types
        species[name] = temp
    return species

def parse_move_list(file):
    dom = xml.dom.minidom.parse(file)
    moves = dict()
    for m in dom.getElementsByTagName("move"):
        move = dict()
        name = m.getAttribute("name")
        move["id"] = int(m.getAttribute("id"))
        move["type"] = get_text(m.getElementsByTagName("type")[0])
        move["class"] = get_text(m.getElementsByTagName("class")[0])
        move["power"] = int(get_text(m.getElementsByTagName("power")[0]))
        move["target"] = get_text(m.getElementsByTagName("target")[0])
        moves[name] = move
    return moves
    