#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        for elem in s.findall("types/type"):
            types.append(elem.text)
        temp["types"] = types
        bases = []
        for elem in s.findall("stats/base"):
            bases.append(int(elem.text))
        temp["bases"] = bases
        abilities = []
        for elem in s.findall("abilities/ability"):
            abilities.append(elem.text)
        temp["abilities"] = types
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
    