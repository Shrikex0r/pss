#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Pixel Starships Research API


# ----- Packages ------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import argparse
import datetime
import re
import os
import pandas as pd
import urllib.request
import uuid
import xml.etree.ElementTree

from pss_core import *

HOME = os.getenv('HOME')
base_url = 'http://{}/'.format(get_production_server())


# ----- Utilities -----------------------------------------------------
def xmltext_to_df(raw_text):
    df = pd.DataFrame()
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        for cc in c:
            for i, ccc in enumerate(cc):
                df = df.append(pd.DataFrame(ccc.attrib, index=[i]))
    return df


def seconds_to_str(sec):
    rt = datetime.timedelta(seconds=int(sec))
    if sec % (24*3600) == 0:
        return '{} days'.format(rt.days)
    else:
        return str(rt)


# ----- Text Conversion -----------------------------------------------
def convert_cost(data):
    cost = []
    if data['GasCost'] > 0:
        cost += ['{}k gas'.format(data['GasCost']//1000)]
    if data['StarbuxCost'] > 0:
        cost += ['{} bux'.format(data['StarbuxCost'])]
    return ', '.join(cost)


def research_to_txt(df):
    if len(df) == 0:
        return None
    elif len(df) == 1:
        data = df.iloc[0, :]
        txt = '{}\n'.format(data['ResearchName'])
        txt += '{}\n'.format(data['ResearchDescription'])
        txt += 'Cost: {}\n'.format(convert_cost(data))
        txt += 'Time: {}\n'.format(seconds_to_str(data['ResearchTime']))
        txt += 'Reqd Lab Lvl: {}'.format(data['RequiredLabLevel'])
        return txt

    txt = ''
    for row in df.iterrows():
        idx, data = row
        rtim = seconds_to_str(data['ResearchTime'])
        txt += '{}: t={}, cost={}\n'.format(
            data['ResearchName'], rtim, convert_cost(data))
    return txt


def filter_researchdf(df, search_str):
    research_lookup = df['ResearchName'].str.lower()
    df_subset = df[research_lookup == search_str.lower()]
    if len(df_subset) == 1:
        return df_subset.copy()
    m = [re.search(search_str.lower(), str(s)) is not None for s in research_lookup ]
    return df[m].copy()


def get_research_designs(format='df'):
    raw_file = 'research-designs-raw.txt'
    url = base_url + 'ResearchService/ListAllResearchDesigns2?languageKey=en'
    raw_text = load_data_from_url(raw_file, url, refresh='auto')
    if format == 'df':
        df_research_designs = xmltext_to_df(raw_text)
        cols = ['Argument', 'GasCost', 'ImageSpriteId', 'LogoSpriteId', 'RequiredItemDesignId',
                'RequiredLabLevel', 'RequiredResearchDesignId', 'ResearchDesignId', 'ResearchTime',
                'StarbuxCost']
        df_research_designs[cols] = df_research_designs[cols].astype(int)
        return df_research_designs
    else:
        return xmltree_to_dict3(raw_text, 'ResearchName')


def get_research_names():
    research = get_research_designs(format='dict')
    research_names = list(research.keys())
    return list_to_text(research_names)


# ----- Rooms ---------------------------------------------------------
def get_room_designs():
    raw_file = 'room-designs-raw.txt'
    url = base_url + 'RoomService/ListRoomDesigns2?languageKey=en'
    raw_text = load_data_from_url(raw_file, url, refresh='auto')
    return xmltree_to_dict3(raw_text, 'RoomName')


def get_room_names():
    rooms = get_room_designs()
    room_names = list(rooms.keys())
    return list_to_text(room_names)


def room_to_txt_description(room, room_names):
    txt = '**{}** (Category: {}, Type: {})\n'.format(
        room['RoomName'], room['CategoryType'], room['RoomType'])
    txt += '{}\n'.format(room['RoomDescription'])
    cost = []
    if room['MineralCost'] != '0':
        cost += ['{} minerals'.format(room['MineralCost'])]
    if room['GasCost'] != '0':
        cost += ['{} gas'.format(room['GasCost'])]

    unit, price = room['PriceString'].split(':')
    txt += 'Construction time: {}, {} Cost: {}\n'.format(
        room['ConstructionTime'], unit, price)
    if room['UpgradeFromRoomDesignId'] != '0':
        txt_room_requirement = ', {}'.format(room_names[room['UpgradeFromRoomDesignId']])
    txt += 'Requires: lvl {} ship\n'.format(room['MinShipLevel'], txt_room_requirement)
    return txt


# ----- Main ----------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'Pixel Starships Research API')
    parser.add_argument('--research', default=None,
        help='Get Research Data')
    parser.add_argument('--rooms', default=None,
        help='Get Room Data')
    args = parser.parse_args()

    if args.research is not None:
        # pss_research.py --research "Ion Core"
        research_str = args.research
        df_research_designs = get_research_designs()
        df_selected = filter_researchdf(df_research_designs, research_str)
        txt = research_to_txt(df_selected)
        print(txt)
    if args.rooms is not None:
        # python3 pss_research.py --rooms "Hangar Lv9"
        rooms = get_room_designs()
        room_names = create_reverse_lookup(rooms, 'RoomDesignId', 'RoomName')
        txt = room_to_txt_description(rooms[args.rooms], room_names)
        print(txt)
        # room_str = args.rooms
        # print(room_str)
