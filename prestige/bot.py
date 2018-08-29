#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Pixel Starships Prestige Bot
#
# 1. Create Discord Bot at:
#    https://discordapp.com/developers/applications/me
# 2. Set Discord Bot permissions at:
#    https://discordapi.com/permissions.html


# ----- Packages ------------------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from discord.ext import commands

import discord
import logging
import os
import pss_dropship as dropship
import pss_fleets as flt
import pss_market as mkt
import pss_prestige as p
import pss_research as rs
import pytz
import time, datetime, holidays


# ----- Setup ---------------------------------------------------------
command_prefix = os.getenv('COMMAND_PREFIX')
BOT_OWNER = os.getenv("DISCORD_BOT_OWNER")
BOT_VERSION = '0.05'
BOT_DESCRIPTION = 'This is a bot for pixel starships'
RATE = 3
COOLDOWN = 30.0

# tbl, rtbl = p.get_char_sheet()
ctbl, tbl_i2n, tbl_n2i, rarity = p.get_char_sheet()
df_research_designs = rs.get_research_designs()

raw_text = mkt.load_item_design_raw()
df_items = mkt.xmltext_to_df(raw_text)
item_rlookup = mkt.get_item_rlookup(df_items)

# welcome_txt = """**Welcome to the Pixel Starships Discord!**
# This is a place where we can interact with devs and players from other alliances/fleets
# 1. :zipper_mouth: you can mute any channel to avoid notifications from that channel
# 2. :microphone: #announcements-and-tips-of-the-day are for anything really important on PSS, as well as a means for the devs to post announcements
# 3. :bulb: if you have any suggestions for the game, you can post them in #suggestion-posts. previously discussed suggestions are in #summaries
# 4. :beetle: #game-support is for bugs, etc. \@@TheRealTiffany is usually there
# 5. :robot: We have a #dolores-bot-room. type “`/help`” to find out how to use this bot for character stats/prestige combos, and item prices/stats.
# 6. :art: Get a Discord color by posting a screenshot with your trophy level in #screenshots
# 7. :dove: The usual guidelines for any forum apply (try to be civil, don’t spam, etc)."""
welcome_txt = """**Welcome to the Pixel Starships Discord!**
This is a place where we can interact with devs and players from other alliances/fleets
1. 🤐 you can mute any channel to avoid notifications from that channel
2. 🎤 #announcements-and-tips-of-the-day are for anything really important on PSS, as well as a means for the devs to post announcements
3. 💡 if you have any suggestions for the game, you can post them in #suggestion-posts. previously discussed suggestions are in #summaries
4. 🐞 #game-support is for bugs, etc. \@@TheRealTiffany is usually there
5. 🤖 We have a #dolores-bot-room. type “`/help`” to find out how to use this bot for character stats/prestige combos, and item prices/stats.
6. 🎨 Get a Discord color by posting a screenshot with your trophy level in #screenshots
7. 🕊 The usual guidelines for any forum apply (try to be civil, don’t spam, etc)."""


# ----- Utilities -----------------------------------------------------
def write_log(log_text, author, server):
    if os.path.isfile("debug") is False:
        return
    time_text = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    ctx_text = '' if ctx is None else \
        '{}@{}'.format(author, server)

    final_text = '{} {}: {}{}'.format(
        time_text, ctx_text, command_prefix, log_text)
    with open("discord-bot.log", "a") as f:
        f.write(final_text + '\n')


# ----- Bot Setup -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    style = '{',
    datefmt = "%Y%m%d %H:%M:%S",
    format = "{asctime} [{levelname:<8}] {name}: {message}")
    # level="INFO")
bot = commands.Bot(command_prefix=command_prefix,
                   description=BOT_DESCRIPTION)
setattr(bot, "logger", logging.getLogger("bot.py"))


# ----- Bot Events ------------------------------------------------------------
@bot.event
async def on_ready():
    print('Bot logged in as {} (id={})'.format(
        bot.user.name, bot.user.id))


@bot.event
async def on_command_error(ctx, err):
    if isinstance(err, commands.CommandOnCooldown):
        await ctx.send('Error: {}'.format(err))


# ----- Bot Commands ----------------------------------------------------------
@bot.command(brief='Ping the server')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def ping(ctx):
    """Ping the server to verify that it\'s listening for commands"""
    await ctx.send('Pong!')


@bot.command(brief='Get prestige combos of crew')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def prestige(ctx, *, name: str=None):
    """Get the prestige combinations of the character specified"""
    if name is None:
        help_txt = 'Enter: {}prestige [character name]'.format(command_prefix)
        await ctx.send(help_txt)
        return

    # write_log(command_prefix + 'prestige {}'.format(name), ctx.author, ctx.server)
    # print("Calling p.prestige({}, 'from', tbl_i2n, tbl_n2i)".format(name))
    prestige_txt, success = p.get_prestige(name, 'from', tbl_i2n, tbl_n2i)
    # print("prestige_txt = {}".format(prestige_txt))
    # print("success = {}".format(success))
    for txt in prestige_txt:
        await ctx.send(txt)


@bot.command(brief='Get character/item recipes')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def recipe(ctx, *, name=None):
    """Get the prestige recipes of a character or ingredients for an item"""
    if name is None:
        help_txt = 'Enter: {}recipe [name]'.format(command_prefix)
        await ctx.send(help_txt)
        return

    # write_log(command_prefix + 'recipe {}'.format(name), ctx.author, ctx.server)
    recipe_found = False

    # Character Recipe
    prestige_txt, success = p.get_prestige(name, 'to', tbl_i2n, tbl_n2i)
    if success is True:
        for txt in prestige_txt:
            await ctx.send(txt)
        recipe_found = True
        return

    # Item Recipe
    content, real_name = mkt.get_item_recipe(name, levels=5)
    if real_name is not None:
        content = '**Recipe for {}**\n'.format(real_name) + content
        content = content + '\n\nNote: bux prices listed here may not always be accurate due to transfers between alts/friends or other reasons'
        await ctx.send(content)
        recipe_found = True

    if recipe_found is False:
        await ctx.send("Could not find character or item named '{}'".format(name))


# @bot.command(brief='Get recent market postings')
# @commands.cooldown(rate=1, per=COOLDOWN, type=commands.BucketType.channel)
# async def market(ctx):
#     """Get a list of items recently posted on the market"""
#     market_txt = mkt.get_market_data()
#     await ctx.send(market_txt)


@bot.command(brief='Get item prices from the PSS API')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def price(ctx, *, item_name=None):
    """Get the average price in bux of the item(s) specified, as returned by the PSS API. Note that prices returned by the API may not reflect the real market value, due to transfers between alts/friends"""
    if item_name is None:
        await ctx.send('Enter: {}price [item name]'.format(command_prefix))
        return

    # write_log(command_prefix + '{} {}'.format(ctx.invoked_with, item_name), ctx.author, ctx.server)
    raw_text = mkt.load_item_design_raw()
    item_lookup = mkt.parse_item_designs(raw_text)

    real_name = mkt.get_real_name(item_name, item_lookup)
    if len(item_name) < 2:
        await ctx.send("Please enter at least two characters for item name")
    elif real_name is not None:
        market_txt = mkt.filter_item_designs(item_name, item_lookup, filter='price')
        market_txt = "**Prices matching '{}'**\n".format(item_name) + market_txt
        market_txt += '\n\nNote: bux prices listed here may not always be accurate due to transfers between alts/friends or other reasons'
        await ctx.send(market_txt)
    else:
        await ctx.send("Could not find item name '{}'".format(item_name))


@bot.command(name='list', brief='List items/characters')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def list(ctx, *, action=''):
    """action=chars: shows all characters
    action=newchars: shows the newest 10 characters that have been added to the game
    action=items: shows all items"""
    # write_log(command_prefix + ctx.invoked_with + ' ' + action, ctx.author, ctx.server)
    txt_list = []
    if action in ['chars', 'newchars']:
        txt_list = p.get_char_list(action)
    elif action == 'items':
        txt_list = mkt.get_item_list()
    elif action == 'research':
        txt_list = rs.get_research_names()
    elif action == 'rooms':
        txt_list = rs.get_room_names()

    for txt in txt_list:
        await ctx.send(txt)


@bot.command(name='stats', aliases=['item'],
    brief='Get item/character stats')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def stats(ctx, *, name=None):
    """Get the stats of a character/crew or item"""
    if name is None:
        await bot.say('Enter: {} [name]'.format(command_prefix + ctx.invoked_with))
        return

    # First try to find a character match
    # (skip this section if command was invoked with 'item'
    if ctx.invoked_with != 'item':
        # write_log('stats {}'.format(name), str(ctx.author), str(ctx.server))
        result = p.get_stats(name, embed=False)
        if result is not None:
            await ctx.send(result)
            found_match = True

    # Next try to find an item match
    # raw_text = mkt.load_item_design_raw()
    # item_lookup = mkt.parse_item_designs(raw_text)
    # market_txt = mkt.filter_item_designs(name, item_lookup, filter='stats')
    market_txt = mkt.get_item_stats(name)
    if market_txt is not None:
        await ctx.send(market_txt)
        found_match = True

    if found_match is False:
        await ctx.send('Could not find {}'.format(name))


# @bot.command()
# async def stats2(ctx, *, name=None):
#     if name is None:
#         await ctx.send('Enter: {}stats [character name]'.format(command_prefix))
#     else:
#         write_log(command_prefix + "stats {}".format(name), ctx)
#         result = p.get_stats(name, embed=True)
#         if result is None:
#             await ctx.send('Could not find {}'.format(name))
#         # else:
#         #     await bot.send_message(ctx.message.channel, embed=result)


@bot.command(brief='Get best items for a slot')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def best(ctx, slot=None, enhancement=None):
    """Get the best enhancement item for a given slot. If multiple matches are found, matches will be shown in descending order."""
    if slot is None:
        txt = 'Enter: {}best [slot] [enhancement]'.format(command_prefix)
        await ctx.send(txt)
        return
    txt = command_prefix + 'best {} {}'.format(slot, enhancement)
    # write_log(txt, ctx.author, ctx.server)

    raw_text = mkt.load_item_design_raw()
    item_lookup = mkt.parse_item_designs(raw_text)
    df_items = mkt.rtbl2items(item_lookup)
    df_filter = mkt.filter_item(
        df_items, slot, enhancement,
        cols=['ItemDesignName', 'EnhancementValue', 'MarketPrice'])

    txt = mkt.itemfilter2txt(df_filter)
    if txt is None:
        await ctx.send('No entries found for {} slot, {} enhancement'.format(
            slot, enhancement))

        str_slots = ', '.join(df_items['ItemSubType'].value_counts().index)
        str_enhancements = ', '.join(df_items['EnhancementType'].value_counts().index)
        txt  = 'Slots: {}\n'.format(str_slots)
        txt += 'Enhancements: {}'.format(str_enhancements)
        await ctx.send(txt)
    else:
        await ctx.send(txt)


@bot.command(brief='Get research data')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def research(ctx, *, research=None):
    """Get the research details on a specific research. If multiple matches are found, only a brief summary will be provided"""
    if research is None:
        txt = 'Enter: {}research [research]'.format(command_prefix)
        await ctx.send(txt)
        return
    txt = command_prefix + 'research {}'.format(research)
    # write_log(txt, ctx.author, ctx.server)

    df_selected = rs.filter_researchdf(df_research_designs, research)
    txt = rs.research_to_txt(df_selected)
    if txt is None:
        await ctx.send("No entries found for '{}'".format(research))
    else:
        await ctx.send(txt)


@bot.command(brief='Get collections')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def collection(ctx, *, collection=None):
    """Get the details on a specific collection."""
    if collection is None:
        txt = 'Enter: {}collection [collection]'.format(command_prefix)
        await ctx.send(txt)
        return
    txt = command_prefix + 'collection {}'.format(collection)
    # write_log(txt, ctx.author, ctx.server)

    print(collection)
    txt = p.show_collection(collection)
    if txt is None:
        await ctx.send("No entries found for '{}'".format(collection))
    else:
        await ctx.send(txt)


@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
@bot.command(hidden=True, brief='Division stars')
async def stars(ctx, *, division=None):
    """Get stars earned by each fleet during final tournament week"""
    if division is None:
        txt = 'Enter: {}stars [division]'.format(command_prefix)
        await ctx.send(txt)
        return
    txt = command_prefix + 'stars {}'.format(division)
    # write_log(txt, ctx.author, ctx.server)
    txt = flt.get_division_stars(division)
    await ctx.send(txt)


# @commands.cooldown(rate=1, per=COOLDOWN, type=commands.BucketType.channel)
# @bot.command(hidden=True, brief='Armor damage')
# async def armor(ctx, *, enhancement=None):
#     """Get armor damage"""
#     txt = command_prefix + 'armor {}'.format(enhancement)
#     # write_log(txt, ctx.author, ctx.server)
#     damage_fraction = 100.0 / (1.0 + float(enhancement)/100.0)
#     txt = "A room enhanced %.1f%% by armor takes a damage of %.1f%% of the base value" % (enhancement, damage_fraction)
#     await ctx.send(txt)


@commands.cooldown(rate=2, per=600.0, type=commands.BucketType.channel)
@bot.command(hidden=True, brief='Show the welcome message')
async def welcome(ctx):
    """Show the welcome message"""
    # write_log('welcome ' + channel, ctx.author, ctx.server)
    await ctx.send(welcome_txt)


@commands.cooldown(rate=2, per=60.0, type=commands.BucketType.channel)
@bot.command(hidden=True, brief='Show the dailies')
async def daily(ctx):
    """Show the dailies"""
    txt = dropship.get_dropship_text()
    await ctx.send(txt)


@bot.command(brief='Get PSS stardate & Melbourne time')
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def time(ctx):
    """Get PSS stardate, as well as the day and time in Melbourne, Australia. Gives the name of the Australian holiday, if it is a holiday in Australia."""
    now = datetime.datetime.now()
    today = datetime.date(now.year, now.month, now.day)
    pss_start = datetime.date(year=2016, month=1, day=6)
    pss_stardate = (today - pss_start).days
    str_time = 'Today is Stardate {}\n'.format(pss_stardate)

    mel_tz = pytz.timezone('Australia/Melbourne')
    mel_time = now.replace(tzinfo=pytz.utc).astimezone(mel_tz)
    str_time += mel_time.strftime('It is %A, %H:%M in Melbourne')

    aus_holidays = holidays.Australia(years=now.year, prov='ACT')
    mel_time = datetime.date(mel_time.year, mel_time.month, mel_time.day)
    if mel_time in aus_holidays:
        str_time += '\nIt is also a holiday ({}) in Australia'.format(aus_holidays[mel_time])
    await ctx.send(str_time)


@bot.command(hidden=True,
    brief='These are testing commands, usually for debugging purposes')
@commands.is_owner()
@commands.cooldown(rate=RATE, per=COOLDOWN, type=commands.BucketType.channel)
async def testing(ctx, *, action=None):
    """These are testing commands, usually for debugging purposes"""
    if action == 'refresh':
        tbl, rtbl = p.get_char_sheet(refresh=True)
        raw_text = mkt.load_item_design_raw(refresh=True)
        await ctx.send('Refreshed')
    elif action == 'restart':
        await ctx.send('Bot will restart')
    elif action == 'info':
        server = ctx.server
        author = ctx.author
        channel = ctx.channel
        txt = 'Server: {} (id={})\n'.format(server, server.id)
        txt += 'Message Author: {} (id={})\n'.format(author, author.id)
        txt += 'This Channel: {} (id={})\n'.format(channel, channel.id)
        txt += 'Discord.py version: {}'.format(discord.__version__)
        await ctx.send(txt)
    elif action == 'say':
        if isinstance(text, str):
            await ctx.send(txt)
    elif action == 'actions':
        print(dir(bot))
        bot_actions = list(dir(bot))
        bot_actions = 'Bot actions:' + ', '.join(bot_actions)
        await ctx.send(bot_actions)

    await bot.delete_message(ctx.message)
    if action == 'restart':
        print('Attempting to restart')
        bot.close()
        quit()


@bot.command(hidden=True, brief='Gives the version number of the bot')
@commands.cooldown(rate=1, per=COOLDOWN, type=commands.BucketType.channel)
async def version(ctx):
    """Gives the version number of the bot"""
    txt = 'Bot version is {}'.format(BOT_VERSION)
    await ctx.send(txt)


if __name__ == '__main__':
    # Running the Discord Bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
