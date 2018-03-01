#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Pixel Starships Market API


# ----- Packages ------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import argparse
import datetime
import csv
import re
import os
import pss_prestige as p
import urllib.request
import uuid
import xml.etree.ElementTree
from io import StringIO


# Discord limits messages to 2000 characters
MESSAGE_CHARACTER_LIMIT = 2000


# ----- Utilities -----------------------------------------------------
def save_raw_text(raw_text, filename):
    with open(filename, 'w') as f:
        f.write(raw_text)


# ----- Get Latest Version --------------------------------------------
def get_latest_version():
    base_url = 'http://api2.pixelstarships.com/'
    url= base_url + 'SettingService/GetLatestVersion?language=Key=en'
    data = urllib.request.urlopen(url).read()
    return data.decode()


# ----- Item Designs --------------------------------------------------
def get_item_designs():
    base_url = 'http://api2.pixelstarships.com/'
    url = base_url + 'ItemService/ListItemDesigns2?languageKey=en'
    data = urllib.request.urlopen(url).read()
    return data.decode()


def save_item_design_raw(raw_text):
    now = datetime.datetime.now()
    filename = 'data/{}.txt'.format(now.strftime('%Y%m%d-%p'))
    save_raw_text(raw_text, filename)


def load_item_design_raw():
    now = datetime.datetime.now()
    filename = 'data/{}.txt'.format(now.strftime('%Y%m%d-%p'))
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            raw_text = f.read()
    else:
        raw_text = get_item_designs()
        save_item_design_raw(raw_text)
    return raw_text


def parse_item_designs(raw_text):
    d = {}
    root = xml.etree.ElementTree.fromstring(raw_text)
    for c in root:
        # print(c.tag) # ListItemDesigns
        for cc in c:
            # print(cc.tag) # ItemDesigns
            for ccc in cc:
                # print(ccc.tag) # ItemDesign
                if ccc.tag != 'ItemDesign':
                    continue

                item_name = ccc.attrib['ItemDesignName']
                d[item_name] = ccc.attrib
    return d


# ----- Parsing -------------------------------------------------------
def fix_item(item):
    # Convert to lower case & non alpha-numeric
    item = re.sub('[^a-z0-9]', '', item.lower())
    item = re.sub('golden', 'gold', item)
    item = re.sub('armour', 'armor', item)
    return item


def filter_item_designs(search_str, rtbl, filter):
    item_original = list(rtbl.keys())
    item_lookup = [ fix_item(s) for s in item_original ]
    item_fixed  = fix_item(search_str)

    txt = ''
    for i, item_name in enumerate(item_lookup):

        m = re.search(item_fixed, item_name)
        if m is not None:
            item_name  = item_original[i]
            d = rtbl[item_name]

            # Filter out items
            if (item_name == 'Gas'            or
                item_name == 'Mineral'        or
                d['MissileDesignId']   != '0' or
                d['CraftDesignId']     != '0' or
                d['CharacterDesignId'] != '0'):
                continue

            # Process
            item_price = d['MarketPrice']
            item_slot  = re.sub('Equipment', '', d['ItemSubType'])
            item_stat  = d['EnhancementType']
            item_stat_value = d['EnhancementValue']

            if filter == 'price':
                if item_price == '0':
                    item_price = 'NA'
                txt += '{}: {}\n'.format(item_name, item_price)
            elif filter == 'stats':
                if item_stat == 'None':
                    continue
                txt += '{}: {} +{} ({})\n'.format(item_name,
                    item_stat, item_stat_value, item_slot)
            else:
                print('Invalid filter')
                quit()

    if len(txt) == 0:
        return None
    else:
        return txt.strip('\n')


# ----- Market Data ---------------------------------------------------
def request_new_market_data(token, subtype='None', rarity='None'):
    # Download Market Data from PSS Servers
    txt_subtype='?itemSubType={}'.format(subtype)
    txt_rarity='&rarity={}'.format(rarity)
    txt_token='&accessToken={}'.format(token)
    base_url = 'http://api2.pixelstarships.com/MessageService/'
    url = base_url +  'ListActiveMarketplaceMessages2' + txt_subtype \
        + txt_rarity + txt_token
    print('url="{}"'.format(url))
    data = urllib.request.urlopen(url).read()
    return data.decode()


def process_market_data(mkt_data):
    # Process Character Sheet to CSV format
    tree = xml.etree.ElementTree.parse(StringIO(mkt_data))
    root = tree.getroot()
    market_txt = ''
    for c in root.findall('ListActiveMarketplaceMessages'):
        for cc in c.findall('Messages'):
            for ccc in cc.findall('Message'):
                mssg_id = ccc.attrib['MessageId']
                user_id = ccc.attrib['UserId']
                message = ccc.attrib['Message']
                user_nm = ccc.attrib['UserName']
                user_sp = ccc.attrib['UserSpriteId']
                mssg_tp = ccc.attrib['MessageType']
                channel = ccc.attrib['ChannelId']
                actv_tp = ccc.attrib['ActivityType']
                actv_ar = ccc.attrib['ActivityArgument']
                mssg_dt = ccc.attrib['MessageDate']
                unit, cost = actv_ar.split(':')
                txt = '{}: {} for {} {}\n'.format(
                    user_nm, message, cost, unit)
                market_txt += txt
    return market_txt


def get_market_data():
    token = str(uuid.uuid4())
    mkt_data = request_new_market_data(token)
    market_txt = process_market_data(mkt_data)
    return market_txt


# ----- Main ----------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'Pixel Starships Market API')
    parser.add_argument('--market', action='store_true',
        help='Get Market Data')
    parser.add_argument('--price',
        help='Get Price on Item')
    args = parser.parse_args()

    if args.market is True:
        print(get_market_data().strip())
    else:
        item_name = args.price
        print('Getting the price of {}'.format(item_name))
        raw_text = load_item_design_raw()
        rtbl = parse_item_designs(raw_text)
        mkt_text = filter_item_designs(item_name, rtbl)
        print(mkt_text)
