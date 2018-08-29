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
import re
import os
import pandas as pd
import urllib.request
import xml.etree.ElementTree
from io import StringIO
from pss_core import *


# Discord limits messages to 2000 characters
MESSAGE_CHARACTER_LIMIT = 2000

base_url = 'http://{}/'.format(get_production_server())


# ----- Character Sheet -----------------------------------------------
def request_new_char_sheet():
    # Download Character Sheet from PSS Servers
    url = base_url + 'CharacterService/ListAllCharacterDesigns?languageKey=en'
    data = urllib.request.urlopen(url).read()
    return data.decode()


def save_char_sheet_raw(char_sheet):
    with open('pss-chars-raw.txt', 'w') as f:
        f.write(char_sheet)


def load_char_sheet_raw(refresh=False):
    if os.path.isfile('pss-chars-raw.txt') and refresh is False:
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


def get_char_sheet(refresh='auto'):
    url = base_url + 'CharacterService/ListAllCharacterDesigns?languageKey=en'
    raw_file = 'pss-chars-raw.txt'
    raw_text = load_data_from_url(raw_file, url, refresh=refresh)
    ctbl = xmltree_to_dict3(raw_text, 'CharacterDesignId')
    tbl_i2n = create_reverse_lookup(ctbl, 'CharacterDesignId', 'CharacterDesignName')
    tbl_n2i = create_reverse_lookup(ctbl, 'CharacterDesignName', 'CharacterDesignId')
    rarity = create_reverse_lookup(ctbl, 'CharacterDesignName', 'Rarity')
    return ctbl, tbl_i2n, tbl_n2i, rarity


def charsheet_to_df(raw_text):
    df = pd.DataFrame()
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root.findall('ListAllCharacterDesigns'):
        for cc in c.findall('CharacterDesigns'):
            for i, ccc in enumerate(cc.findall('CharacterDesign')):
                row = pd.DataFrame(ccc.attrib, index=[i])
                df = df.append(row)
    df['CharacterDesignId'] = df['CharacterDesignId'].astype(int)
    return df


# ----- Parsing -------------------------------------------------------
def fix_char(char):
    # Convert to lower case & non alpha-numeric
    char = re.sub('[^a-z0-9]', '', char.lower())
    char = re.sub("captain", "captn", char)
    char = re.sub("lolita", "lollita", char)
    return char


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
            return rtbl[char_name], char_name
        else:
            print("char2id(): could not find the character '{}'".format(char))
            return None, char
    else:
        return char, char


# ----- Prestige API --------------------------------------------------
def get_prestige_data_from_url(char_id, action):
    if action == 'to':
        url = base_url + 'CharacterService/PrestigeCharacterTo?characterDesignId={}'.format(char_id)
        attrib = 'PrestigeCharacterTo'
    elif action == 'from':
        url = base_url + 'CharacterService/PrestigeCharacterFrom?characterDesignId={}'.format(char_id)
        attrib = 'PrestigeCharacterFrom'
    else:
        print('action = "{}" is invalid'.format(action))
        return None
    return get_data_from_url(url)


def xmltree_to_prestige_dict(raw_text):
    ptbl = []
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        for cc in c:
            for p in cc:
                char_id1 = p.attrib['CharacterDesignId1']
                char_id2 = p.attrib['CharacterDesignId2']
                char_new = p.attrib['ToCharacterDesignId']
                ptbl.append([char_id1, char_id2, char_new])
    return ptbl


def prestige_tbl_to_txt(ptbl, tbl_i2n, direction):
    # direction = to, from, or full (default)

    txt = ''
    txt_list = []
    for i, row in enumerate(ptbl):
        c1 = row[0]
        c2 = row[1]
        c3 = row[2]
        if c1 in tbl_i2n.keys():
            c1 = tbl_i2n[c1]
        if c2 in tbl_i2n.keys():
            c2 = tbl_i2n[c2]
        if c3 in tbl_i2n.keys():
            c3 = tbl_i2n[c3]
        # print('{}: {} + {} -> {}'.format(i, c1, c2, c3))
        if direction == "to":
            line = '{} + {}'.format(c1, c2)
        elif direction == "from":
            line = '+ {} -> {}'.format(c2, c3)
        else:
            line = '{} + {} -> {}'.format(c1, c2, c3)

        if i > 0:
            line = '\n' + line
        if len(txt+line) > MESSAGE_CHARACTER_LIMIT:
            txt_list.append(txt)
            txt = line
        else:
            txt += line

    txt_list.append(txt)
    return txt_list


def get_prestige(char_input, direction, tbl_i2n, tbl_n2i):
    char_id, char_fixed = char2id(char_input, tbl_n2i)
    if char_id is None:
        return ["Character '{}' not found".format(char_fixed)], False

    raw_text = get_prestige_data_from_url(char_id, direction)
    ptbl = xmltree_to_prestige_dict(raw_text)
    if len(ptbl) == 0:
        return ["No prestige combinations found for '{}'".format(char_fixed)], False

    if direction == "to":
        prestige_txt = ['**{}** can be prestiged from:'.format(char_fixed)]
    elif direction == "from":
        prestige_txt = ['**{}**'.format(char_fixed)]

    prestige_txt += prestige_tbl_to_txt(ptbl, tbl_i2n, direction)
    return prestige_txt, True


def show_new_chars(action='prestige'):
    tbl1, rtbl1 = load_char_sheet('pss-chars.txt')
    _, tbl2, rtbl2, _ = get_char_sheet()
    # ctbl, tbl_i2n, tbl_n2i, rarity = get_char_sheet()
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


def print_stats(d, char_input):
    char_name = parse_char_name(char_input, tbl_n2i)
    if char_name is None:
        return None

    stats = d[char_name]
    special = stats['SpecialAbilityType']
    if special in specials_lookup.keys():
        special = specials_lookup[special]
    eqpt_mask = convert_eqpt_mask(int(stats['EquipmentMask']))
    coll_id   = stats['CollectionDesignId']
    if coll_id in collections.keys():
        coll_name = collections[coll_id]['CollectionName']
    else:
        coll_name = 'None'

    txt = '**{}** ({})\n'.format(char_name, stats['Rarity'])
    txt += '{}\n'.format(stats['CharacterDesignDescription'])

    txt += 'Race: {}, Collection: {}, Gender: {}\n'.format(
        stats['RaceType'], coll_name, stats['GenderType'])
    txt += 'ability = {} ({})\n'.format(stats['SpecialAbilityFinalArgument'], special)
    txt += 'hp = {}\n'.format(stats['FinalHp'])
    txt += 'attack = {}\n'.format(stats['FinalAttack'])
    txt += 'repair = {}\n'.format(stats['FinalRepair'])
    txt += 'pilot = {}\n'.format(stats['FinalPilot'])
    txt += 'science = {}\n'.format(stats['FinalScience'])
    txt += 'weapon = {}\n'.format(stats['FinalWeapon'])
    txt += 'engine = {}\n'.format(stats['FinalEngine'])
    txt += 'walk/run speed = {}/{}\n'.format(stats['WalkingSpeed'], stats['RunSpeed'])
    txt += 'fire resist = {}\n'.format(stats['FireResistance'])
    txt += 'training capacity = {}\n'.format(stats['TrainingCapacity'])
    txt += 'equipment = {}'.format(eqpt_mask)
    return txt


# def embed_stats(d, char):
#     char_name = parse_char_name(char, rtbl)
#     if char_name is None:
#         return None
#
#     stats = d[char_name]
#     special = stats['SpecialAbilityType']
#     if special in specials_lookup.keys():
#         special = specials_lookup[special]
#     eqpt_mask = convert_eqpt_mask(int(stats['EquipmentMask']))
#
#     embed = discord.Embed(
#         title='**{}** ({})\n'.format(char_name, stats['Rarity']),
#         description=stats['CharacterDesignDescription'], color=0x00ff00)
#     embed.add_field(name="Race", value=stats['RaceType'], inline=False)
#     embed.add_field(name="Gender", value=stats['GenderType'], inline=False)
#     embed.add_field(name="hp", value=stats['FinalHp'], inline=False)
#     embed.add_field(name="attack", value=stats['FinalAttack'], inline=False)
#     embed.add_field(name="repair", value=stats['FinalRepair'], inline=False)
#     embed.add_field(name="ability", value=stats['SpecialAbilityFinalArgument'], inline=False)
#     embed.add_field(name="pilot", value=stats['FinalPilot'], inline=False)
#     embed.add_field(name="shield", value=stats['FinalShield'], inline=False)
#     embed.add_field(name="weapon", value=stats['FinalWeapon'], inline=False)
#     embed.add_field(name="engine", value=stats['FinalEngine'], inline=False)
#     embed.add_field(name="run speed", value=stats['RunSpeed'], inline=False)
#     embed.add_field(name="fire resist", value=stats['FireResistance'], inline=False)
#     embed.add_field(name="special", value=special, inline=False)
#     embed.add_field(name="equipment", value=eqpt_mask, inline=False)
#     return embed

# ----- Collections ---------------------------------------------------
def get_collections():
    raw_file = 'pss-collections-raw.txt'
    url = base_url + 'CollectionService/ListAllCollectionDesigns'
    raw_text = load_data_from_url(raw_file, url, refresh='auto')
    collections = xmltree_to_dict3(raw_text, 'CollectionDesignId')
    collection_names = create_reverse_lookup(collections, 'CollectionDesignId', 'CollectionName')
    return collections, collection_names


def get_characters_in_collection(collection_id):
    raw_file = 'pss-chars-raw.txt'
    url = base_url + 'CharacterService/ListAllCharacterDesigns?languageKey=en'
    raw_text = load_data_from_url(raw_file, url, refresh='auto')
    tbl = xmltree_to_dict3(raw_text, 'CharacterDesignId')

    chars_in_collection = []
    for k in tbl.keys():
        c = tbl[k]
        if int(c['CollectionDesignId']) == int(collection_id):
            char_name = c['CharacterDesignName']
            chars_in_collection.append(char_name)
    return chars_in_collection


def show_collection(search_str):
    raw_file = 'pss-collections-raw.txt'
    url = base_url + 'CollectionService/ListAllCollectionDesigns'
    raw_text = load_data_from_url(raw_file, url, refresh='auto')
    collections = xmltree_to_dict3(raw_text, 'CollectionDesignId')
    collection_names = create_reverse_lookup(collections, 'CollectionDesignId', 'CollectionName') #id2names
    collection_ids = create_reverse_lookup(collections, 'CollectionName', 'CollectionDesignId') #names2id

    real_name = get_real_name(search_str, list(collection_ids.keys()))
    idx = collection_ids[real_name]
    chars_in_collection = get_characters_in_collection(idx)

    c = collections[idx]
    txt = ''
    txt += '**{}** ({})\n'.format(c['CollectionName'], c['CollectionType'])
    txt += '{}\n'.format(c['CollectionDescription'])
    txt += 'Combo Min/Max: {}...{}\n'.format(c['MinCombo'], c['MaxCombo'])
    txt += '{}: '.format(c['EnhancementType'])
    txt += '{} (Base), {} (Step)\n'.format(c['BaseEnhancementValue'], c['StepEnhancementValue'])
    txt += 'Characters: {}'.format(', '.join(chars_in_collection))
    return txt


# ----- List ----------------------------------------------------------
def get_char_list(action):
    if action == 'newchars' or action == 'chars':
        char_sheet_raw = load_char_sheet_raw(refresh=True)
        char_df = charsheet_to_df(char_sheet_raw)
        char_df = char_df.sort_values('CharacterDesignId', ascending=True)

    if action == 'newchars':
        with open('pss-last-char.txt') as f:
            last_char = int(f.read().strip())
            # print('Last character = {}'.format(last_char))

        cols = ['CharacterDesignId', 'CharacterDesignName']
        char_df['CharacterDesignId'] = char_df['CharacterDesignId'].astype(int)
        new_chars = char_df.loc[char_df['CharacterDesignId'] > last_char, cols]

        txt = ''
        for i, row in enumerate(new_chars.iterrows()):
            data = row[1]
            txt += '{:3}: {}\n'.format(data['CharacterDesignId'], data['CharacterDesignName'])
        return [txt]

    elif action == 'chars':
        names = list(char_df['CharacterDesignName'].values)
        print('List of characters: ' + ', '.join(names))
        txt_list = list_to_text(names)
        return txt_list


# ----- Setup ---------------------------------------------------------
ctbl, tbl_i2n, tbl_n2i, rarity = get_char_sheet()
collections, collection_names = get_collections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Pixel Starships Prestige & Character Sheet API')
    parser.add_argument('prestige',
        choices=['to', 'from', 'stats', 'refresh', 'collection', 'list'],
        help='Prestige direction (to/from character)')
    parser.add_argument('character', help='Character to prestige')
    args = parser.parse_args()

    if args.prestige == 'refresh':
        ctbl, tbl_i2n, tbl_n2i, rarity = get_char_sheet()
    elif args.prestige == 'stats':
        result = get_stats(args.character, embed=False)
        print(result)
        # print_stats(rtbl, args.character)
    elif args.prestige == 'collection':
        txt = show_collection(args.character)
        print(txt)
    elif args.prestige == 'list':
        # python3 pss_prestige.py list chars
        # python3 pss_prestige.py list newchars
        txt_list = get_char_list(action=args.character)
        for txt in txt_list:
            print(txt)
    else:
        # python3 pss_prestige.py to 'Alien Queen'
        prestige_txt, success = get_prestige(
            args.character, args.prestige, tbl_i2n, tbl_n2i)
        if success is True:
            for txt in prestige_txt:
                print(txt)
