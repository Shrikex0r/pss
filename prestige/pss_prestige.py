#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Pixel Starships Prestige & Character Sheet API


# ----- Packages ------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import argparse
import csv
import discord
import re
import os
import urllib.request
import xml.etree.ElementTree
from io import StringIO


# Discord limits messages to 2000 characters
MESSAGE_CHARACTER_LIMIT = 2000


# ----- Character Sheet -----------------------------------------------
def request_new_char_sheet():
    # Download Character Sheet from PSS Servers
    url = 'https://api2.pixelstarships.com/CharacterService/ListAllCharacterDesigns?languageKey=en'
    data = urllib.request.urlopen(url).read()
    return data.decode()


def save_char_sheet_raw(char_sheet):
    with open('pss-chars-raw.txt', 'w') as f:
        f.write(char_sheet)


def load_char_sheet_raw():
    if os.path.isfile('pss-chars-raw.txt'):
        with open('pss-chars-raw.txt', 'r') as f:
            raw_text = f.read()
    else:
        raw_text = request_new_char_sheet()
        save_char_sheet_raw(raw_text)
    return raw_text


def save_char_sheet(char_sheet,
                    filename='pss-chars.txt'):
    # Process Character Sheet to CSV format
    tree = xml.etree.ElementTree.parse(StringIO(char_sheet))
    root = tree.getroot()
    tbl = {}
    rtbl = {}
    rarity = {}
    for c in root.findall('ListAllCharacterDesigns'):
        for cc in c.findall('CharacterDesigns'):
            for ccc in cc.findall('CharacterDesign'):
                char_id = ccc.attrib['CharacterDesignId']
                char_dn = ccc.attrib['CharacterDesignName']
                rarity = ccc.attrib['Rarity']
                tbl[char_id] = char_dn
                rtbl[char_dn] = char_id

    # Save Character Sheet to text file
    with open(filename, 'w') as f:
        for key in tbl.keys():
            f.write('{},{}\n'.format(key, tbl[key]))
    return tbl, rtbl


def load_char_sheet(filename='pss-chars.txt'):
    # Load character sheet from text file
    with open(filename, 'r') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        tbl = {}
        rtbl = {}
        for row in readCSV:
            char_id = row[0]
            char_dn = row[1]
            tbl[char_id] = char_dn
            rtbl[char_dn] = char_id
    return tbl, rtbl


def get_char_sheet(refresh=False):
    if refresh == False and os.path.isfile('pss-chars.txt'):
        tbl, rtbl = load_char_sheet()
    else:
        char_sheet = request_new_char_sheet()
        save_char_sheet_raw(char_sheet)
        tbl, rtbl = save_char_sheet(char_sheet)
    return tbl, rtbl


# ----- Parsing -------------------------------------------------------
def fix_char(char):
    # Convert to lower case & non alpha-numeric
    return re.sub('[^a-z0-9]', '', char.lower())


def parse_char_name(char, rtbl):
    char_original = list(rtbl.keys())
    char_lookup = [ fix_char(s) for s in char_original ]
    char_fixed  = fix_char(char)

    # 1. Look for an exact match
    if char_fixed in char_lookup:
        idx = char_lookup.index(char_fixed)
        return char_original[idx]

    # 2. Perform a search instead
    m = [ re.search(char_fixed, s) is not None for s in char_lookup ]
    if sum(m) > 0:
        # idx = m.index(True)  # forward search for match
        idx = len(m)-1 - m[::-1].index(True)  # reverse search
        return char_original[idx]
    return None


def char2id(char, rtbl):
    if isinstance(char, str):
        char_name = parse_char_name(char, rtbl)
        if char_name is not None:
            return rtbl[char_name]
        else:
            print("Could not find {}".format(char))
            return None
    else:
        return char


# ----- Prestige API --------------------------------------------------
def get_prestige_data(char, action, rtbl):
    char_id = char2id(char, rtbl)
    if char_id is None:
        return None, None

    if action == 'to':
        url = 'http://api2.pixelstarships.com/CharacterService/PrestigeCharacterTo?characterDesignId={}'.format(char_id)
        attrib = 'PrestigeCharacterTo'
    elif action == 'from':
        url = 'http://api2.pixelstarships.com/CharacterService/PrestigeCharacterFrom?characterDesignId={}'.format(char_id)
        attrib = 'PrestigeCharacterFrom'
    else:
        print('action = "{}" is invalid'.format(action))
        return None, None
    data = urllib.request.urlopen(url).read()
    content = data.decode()

    tree = xml.etree.ElementTree.parse(StringIO(content))
    root = tree.getroot()

    tbl = []
    for c in root.findall(attrib):
        for cc in c.findall('Prestiges'):
            for p in cc.findall('Prestige'):
                char_id1 = p.attrib['CharacterDesignId1']
                char_id2 = p.attrib['CharacterDesignId2']
                char_new = p.attrib['ToCharacterDesignId']
                tbl.append([char_id1, char_id2, char_new])
    return content, tbl


def get_prestige_text(ptbl, tbl, direction):
    # direction = to, from, or full (default)

    if direction == "to":
        char_name = tbl[ptbl[0][2]]
        txt = '**{}** can be prestiged from:\n'.format(char_name)
    elif direction == "from":
        char_name = tbl[ptbl[0][0]]
        txt = '**{}**\n'.format(char_name)

    txt_list = []
    for i, row in enumerate(ptbl):
        if direction == "to":
            line = '{} + {}'.format(tbl[row[0]], tbl[row[1]])
        elif direction == "from":
            line = '+ {} -> {}'.format(tbl[row[1]], tbl[row[2]])
        else:
            line = '{} + {} -> {}'.format(tbl[row[0]], tbl[row[1]], tbl[row[2]])

        if i > 0:
            line = '\n' + line
        if len(txt+line) > MESSAGE_CHARACTER_LIMIT:
            txt_list.append(txt)
            txt = line
        else:
            txt += line

    txt_list.append(txt)
    return txt_list


def show_new_chars(action='prestige'):
    tbl1, rtbl1 = load_char_sheet('pss-chars.txt')
    tbl2, rtbl2 = get_char_sheet(refresh=True)
    old_ids = tbl1.keys()
    new_ids = tbl2.keys()
    new_chars = False
    for ii in new_ids:
        if ii not in old_ids:
            if action == 'prestige':
                content, ptbl = get_prestige_data(
                    tbl2[ii], 'from', rtbl2)
                print_prestige_formulas(ptbl, tbl2)
            else:
                print('{}'.format(tbl2[ii]))
            new_chars = True
    return new_chars


# ----- Stats Conversion ----------------------------------------------
specials_lookup = {
    'AddReload': 'Rush Command',
    'DamageToCurrentEnemy': 'Critical Strike',
    'DamageToRoom': 'Ultra Dismantle',
    'DamageToSameRoomCharacters': 'Poison Gas',
    'DeductReload': 'System Hack',
    'FireWalk': 'Fire Walk',
    'Freeze': 'Freeze',
    'HealRoomHp': 'Urgent Repair',
    'HealSameRoomCharacters': 'Healing Rain',
    'HealSelfHp': 'First Aid',
    'SetFire': 'Arson'}


equipment_lookup = {
    1: 'head',
    2: 'body',
    4: 'leg',
    8: 'weapon',
    16: 'accessory'}


def convert_eqpt_mask(eqpt_mask):
    eqpt_list = []
    for k in equipment_lookup.keys():
        if (eqpt_mask & k) != 0:
            eqpt_list = eqpt_list + [equipment_lookup[k]]
    if len(eqpt_list) == 0:
        return 'nil'
    else:
        return ', '.join(eqpt_list)


# ----- Stats API -----------------------------------------------------
def stats2dict(raw_text):
    d = {}
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        for cc in c:
            for ccc in cc:
                if ccc.tag != 'CharacterDesign':
                    continue
                char_name = ccc.attrib['CharacterDesignName']
                d[char_name] = ccc.attrib
    return d


def get_stats(char_name, embed=False):
    raw_text = load_char_sheet_raw()
    d = stats2dict(raw_text)
    if embed is True:
        return embed_stats(d, char_name)
    else:
        return print_stats(d, char_name)


def print_stats(d, char):
    char_name = parse_char_name(char, rtbl)
    if char_name is None:
        return None

    stats = d[char_name]
    special = stats['SpecialAbilityType']
    if special in specials_lookup.keys():
        special = specials_lookup[special]
    eqpt_mask = convert_eqpt_mask(int(stats['EquipmentMask']))

    txt = '**{}** ({})\n'.format(char_name, stats['Rarity'])
    txt += '{}\n'.format(stats['CharacterDesignDescription'])

    txt += 'Race: {}, Gender: {}\n'.format(
        stats['RaceType'], stats['GenderType'])
    txt += 'ability = {}\n'.format(stats['SpecialAbilityFinalArgument'])
    txt += 'hp = {}\n'.format(stats['FinalHp'])
    txt += 'attack = {}\n'.format(stats['FinalAttack'])
    txt += 'repair = {}\n'.format(stats['FinalRepair'])
    txt += 'pilot = {}\n'.format(stats['FinalPilot'])
    txt += 'shield = {}\n'.format(stats['FinalShield'])
    txt += 'weapon = {}\n'.format(stats['FinalWeapon'])
    txt += 'engine = {}\n'.format(stats['FinalEngine'])
    txt += 'walk/run speed = {}/{}\n'.format(stats['WalkingSpeed'], stats['RunSpeed'])
    txt += 'fire resist = {}\n'.format(stats['FireResistance'])
    txt += 'training capacity = {}\n'.format(stats['TrainingCapacity'])
    txt += 'special = {}\n'.format(special)
    txt += 'equipment = {}'.format(eqpt_mask)
    return txt


def embed_stats(d, char):
    char_name = parse_char_name(char, rtbl)
    if char_name is None:
        return None

    stats = d[char_name]
    special = stats['SpecialAbilityType']
    if special in specials_lookup.keys():
        special = specials_lookup[special]
    eqpt_mask = convert_eqpt_mask(int(stats['EquipmentMask']))

    embed = discord.Embed(
        title='**{}** ({})\n'.format(char_name, stats['Rarity']),
        description=stats['CharacterDesignDescription'], color=0x00ff00)
    embed.add_field(name="Race", value=stats['RaceType'], inline=False)
    embed.add_field(name="Gender", value=stats['GenderType'], inline=False)
    embed.add_field(name="hp", value=stats['FinalHp'], inline=False)
    embed.add_field(name="attack", value=stats['FinalAttack'], inline=False)
    embed.add_field(name="repair", value=stats['FinalRepair'], inline=False)
    embed.add_field(name="ability", value=stats['SpecialAbilityFinalArgument'], inline=False)
    embed.add_field(name="pilot", value=stats['FinalPilot'], inline=False)
    embed.add_field(name="shield", value=stats['FinalShield'], inline=False)
    embed.add_field(name="weapon", value=stats['FinalWeapon'], inline=False)
    embed.add_field(name="engine", value=stats['FinalEngine'], inline=False)
    embed.add_field(name="run speed", value=stats['RunSpeed'], inline=False)
    embed.add_field(name="fire resist", value=stats['FireResistance'], inline=False)
    embed.add_field(name="special", value=special, inline=False)
    embed.add_field(name="equipment", value=eqpt_mask, inline=False)
    return embed


# ----- Setup ---------------------------------------------------------
tbl, rtbl = get_char_sheet(refresh=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'Pixel Starships Prestige & Character Sheet API')
    parser.add_argument('prestige', choices=['to', 'from'],
        help='Prestige direction (to/from character)')
    parser.add_argument('character', help='Character to prestige')
    args = parser.parse_args()

    content, ptbl = get_prestige_data(args.character, args.prestige, rtbl)
    prestige_text = get_prestige_text(ptbl, tbl, args.prestige)
    for txt in prestige_text:
        print(txt)
