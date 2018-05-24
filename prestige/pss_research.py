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


HOME = os.getenv('HOME')


# ----- Utilities -----------------------------------------------------
def get_data_from_url(url):
    data = urllib.request.urlopen(url).read()
    return data.decode()


def save_raw_text(raw_text, filename):
    with open(filename, 'w') as f:
        f.write(raw_text)
        
def load_data_from_url(filename, url, refresh=False):
    if os.path.isfile(filename) and refresh is False:
        with open(filename, 'r') as f:
            raw_text = f.read()
    else:
        raw_text = get_data_from_url(url)
        save_raw_text(raw_text, filename)
    return raw_text


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


def get_research_designs():
    url_research_designs = 'http://api.pixelstarships.com/ResearchService/ListAllResearchDesigns2?languageKey=en'
    research_designs = load_data_from_url('research-designs-raw.txt', url_research_designs)
    df_research_designs = xmltext_to_df(research_designs)
    cols = ['Argument', 'GasCost', 'ImageSpriteId', 'LogoSpriteId', 'RequiredItemDesignId',
            'RequiredLabLevel', 'RequiredResearchDesignId', 'ResearchDesignId', 'ResearchTime',
            'StarbuxCost']
    df_research_designs[cols] = df_research_designs[cols].astype(int)
    return df_research_designs


# ----- Main ----------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'Pixel Starships Research API')
    parser.add_argument('--research',
        help='Get Research Data')
    args = parser.parse_args()

    research_str = args.research
    df_research_designs = get_research_designs()
    df_selected = filter_researchdf(df_research_designs, research_str)
    txt = research_to_txt(df_selected)
    print(txt)

