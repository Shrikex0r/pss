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
import os
import logging
import pss_market as mkt
import pss_prestige as p
import pss_research as rs
import pytz
import time, datetime, holidays


# ----- Setup ---------------------------------------------------------
command_prefix = os.getenv('COMMAND_PREFIX')
BOT_OWNER = os.getenv("DISCORD_BOT_OWNER")
BOT_VERSION = '0.02'

tbl, rtbl = p.get_char_sheet()
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
def get_channel_from_str(server, channel_str):
    for i, channel in enumerate(server.channels):
        # txt += '{}: Channel: {} (id={})'.format(i, channel.name, channel.id)
        if channel.name == channel_str:
            return channel
    return None


def write_log(log_text, ctx=None):
    if os.path.isfile("debug") is False:
        return
    time_text = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    ctx_text = '' if ctx is None else \
        '{}@{}'.format(ctx.message.author, ctx.message.server)

    final_text = '{} {}: {}'.format(time_text, ctx_text, log_text)
    with open("discord-bot.log", "a") as f:
        f.write(final_text + '\n')
    print(final_text)


# ----- Bot -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    style = '{',
    datefmt = "%Y%m%d %H:%M:%S",
    format = "{asctime} [{levelname:<8}] {name}: {message}")
bot = commands.Bot(description='This is a bot for pixel starships',
    command_prefix=command_prefix)


@bot.event
async def on_ready():
    write_log('Hi, bot logged in as {}'.format(bot.user.name))


@bot.event
async def on_command_error(err, ctx):
    if isinstance(err, commands.CommandOnCooldown):
        await bot.send_message(ctx.message.channel, 'Error: {}'.format(err))


@bot.event
async def on_member_join(member):
    print('MEMBER JOINED {} | {} Joined: {}'.format(member.name, member.id, member.server))
    if member.server == 'Pixel Starships':
        await bot.send_message(member, welcome_txt)


@bot.event
async def on_reaction_add(reaction, user):
    write_log('Reaction {} added by {}'.format(reaction, user))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(brief='Ping the server to verify that it\'s listening for commands',
             description='Ping the server to verify that it\'s listening for commands')
async def ping():
    await bot.say('Pong!')


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True,
    brief='Get the prestige combinations of the character specified',
    description='Get the prestige combinations of the character specified')
async def prestige(ctx, *, char_name=None):
    if char_name is None:
        help_txt = 'Enter: {}prestige [character name]'.format(command_prefix)
        await bot.say(help_txt)
    else:
        write_log(command_prefix + 'prestige {}'.format(char_name), ctx)
        content, ptbl = p.get_prestige_data(char_name, 'from', rtbl)
        if content is None:
            await bot.say("Could not find {}".format(char_name))
        else:
            prestige_text = p.get_prestige_text(ptbl, tbl, 'from')
            try:
                for txt in prestige_text:
                    await bot.say(txt)
            except:
                write_log('Failed to send the following to bot')
                write_log('"{}"'.format(prestige_text))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True,
    brief='Get the recipes for a character/item',
    description='Get the prestige recipes of a character or ingredients for an item')
async def recipe(ctx, *, name=None):
    if name is None:
        help_txt = 'Enter: {}recipe [name]'.format(command_prefix)
        await bot.say(help_txt)
        return

    write_log(command_prefix + 'recipe {}'.format(name), ctx)
    recipe_found = False

    # Character Recipe
    content, ptbl = p.get_prestige_data(name, 'to', rtbl)
    if content is not None:
        prestige_text = p.get_prestige_text(ptbl, tbl, 'to')
        try:
            for txt in prestige_text:
                await bot.say(txt)
        except:
            write_log('Failed to send the following to bot')
            write_log('"{}"'.format(prestige_text))
        recipe_found = True
        return

    # Item Recipe
    raw_text = mkt.load_item_design_raw()
    item_lookup = mkt.parse_item_designs(raw_text)
    real_name = mkt.get_real_name(name, item_lookup)
    if real_name is not None:
        content = '**Recipe for {}**\n'.format(real_name)
        content = content + mkt.get_multi_recipe(real_name, levels=3)
        await bot.say(content)
        recipe_found = True

    if recipe_found is False:
        await bot.say('Could not find {}'.format(name))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True,
    brief='Get a list of items recently posted on the market',
    description='Get a list of items recently posted on the market')
async def market(ctx):
    market_txt = mkt.get_market_data()
    try:
        await bot.say(market_txt)
    except:
        write_log('Failed to send the following to bot')
        write_log('"{}"'.format(market_txt))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True, brief='Get the average price in bux of the item(s) specified.',
             description='Get the average price in bux of the item(s) specified, as returned by the PSS API. ' +
             'Note that prices returned by the API may not reflect the real market value, ' +
             'due to transfers between alts/friends')
async def price(ctx, *, item_name=None):
    if item_name is None:
        await bot.say('Enter: {}price [item name]'.format(command_prefix))
        return

    write_log(command_prefix + '{} {}'.format(ctx.invoked_with, item_name), ctx)
    raw_text = mkt.load_item_design_raw()
    item_lookup = mkt.parse_item_designs(raw_text)

    real_name = mkt.get_real_name(item_name, item_lookup)
    if real_name is not None:
        market_txt = mkt.filter_item_designs(item_name, item_lookup, filter='price')
        market_txt = '**Prices as returned by the PSS API**\n' + market_txt
        await bot.say(market_txt)
    else:
        await bot.say('{} not found'.format(item_name))


def list_to_text(lst, max_chars=1900):
    txt_list = []
    txt = ''
    for i, item in enumerate(lst):
        if len(txt) > max_chars:
            txt_list += [txt]
            txt = item
        elif i == 0:
            txt = item
        else:
            txt += ', ' + item

    txt_list += [txt]
    return txt_list


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(name='list', pass_context=True,
             brief='List items/characters',
             description='action=chars: shows all characters\naction=newchars: shows the newest 10 characters that have been added to the game\naction=items: shows all items')
async def list(ctx, *, action=''):
    write_log(command_prefix + ctx.invoked_with + ' ' + action, ctx)
    if action == 'newchars' or action == 'chars':
        txt_list = p.get_char_list(action)
    elif action == 'items':
        txt_list = mkt.get_item_list()

    for txt in txt_list:
        await bot.say(txt)


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(name='stats', aliases=['item'], pass_context=True,
             brief='Get the stats of a character or item',
             description='Get the stats of a character/crew or item')
async def stats(ctx, *, name=None):
    if name is None:
        await bot.say('Enter: {} [name]'.format(command_prefix + ctx.invoked_with))
        return

    # First try to find a character match
    # (skip this section if command was invoked with 'item'
    if ctx.invoked_with != 'item':
        write_log(command_prefix + 'stats {}'.format(name), ctx)
        result = p.get_stats(name, embed=False)
        if result is not None:
            await bot.say(result)
            found_match = True

    # Next try to find an item match
    raw_text = mkt.load_item_design_raw()
    item_lookup = mkt.parse_item_designs(raw_text)
    market_txt = mkt.filter_item_designs(name, item_lookup, filter='stats')
    if market_txt is not None:
        market_txt = '**Item Stats**\n' + market_txt
        await bot.say(market_txt)
        found_match = True

    if found_match is False:
        await bot.say('Could not find {}'.format(name))


# @bot.command(pass_context=True)
# async def stats2(ctx, *, char_name=None):
#     if char_name is None:
#         await bot.say('Enter: {}stats [character name]'.format(command_prefix))
#     else:
#         write_log(command_prefix + "stats {}".format(char_name), ctx)
#         result = p.get_stats(char_name, embed=True)
#         if result is None:
#             await bot.say('Could not find {}'.format(char_name))
#         else:
#             await bot.send_message(ctx.message.channel, embed=result)


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True,
    brief='Get the best enhancement item for a given slot',
    description='Get the best enhancement item for a given slot. ' +
        'If multiple matches are found, matches will be shown in descending order')
async def best(ctx, slot=None, enhancement=None):
    if slot is None:
        txt = 'Enter: {}best [slot] [enhancement]'.format(command_prefix)
        await bot.say(txt)
        return
    txt = command_prefix + 'best {} {}'.format(slot, enhancement)
    write_log(txt, ctx)

    raw_text = mkt.load_item_design_raw()
    item_lookup = mkt.parse_item_designs(raw_text)
    df_items = mkt.rtbl2items(item_lookup)
    df_filter = mkt.filter_item(
        df_items, slot, enhancement,
        cols=['ItemDesignName', 'EnhancementValue', 'MarketPrice'])

    txt = mkt.itemfilter2txt(df_filter)
    if txt is None:
        await bot.say('No entries found for {} slot, {} enhancement'.format(
            slot, enhancement))

        str_slots = ', '.join(df_items['ItemSubType'].value_counts().index)
        str_enhancements = ', '.join(df_items['EnhancementType'].value_counts().index)
        txt  = 'Slots: {}\n'.format(str_slots)
        txt += 'Enhancements: {}'.format(str_enhancements)
        await bot.say(txt)
    else:
        await bot.say(txt)


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True,
    brief='Get research data',
    description='Get the research details on a specific research. ' +
        'If multiple matches are found, only a brief summary will be provided')
async def research(ctx, *, research=None):
    if research is None:
        txt = 'Enter: {}research [research]'.format(command_prefix)
        await bot.say(txt)
        return
    txt = command_prefix + 'research {}'.format(research)
    write_log(txt, ctx)

    df_selected = rs.filter_researchdf(df_research_designs, research)
    txt = rs.research_to_txt(df_selected)
    if txt is None:
        await bot.say("No entries found for '{}'".format(research))
    else:
        await bot.say(txt)


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True,
    brief='Get collections',
    description='Get the details on a specific collection.')
async def collection(ctx, *, collection=None):
    if collection is None:
        txt = 'Enter: {}collection [collection]'.format(command_prefix)
        await bot.say(txt)
        return
    txt = command_prefix + 'collection {}'.format(collection)
    write_log(txt, ctx)

    print(collection)
    txt = p.show_collection(collection)
    if txt is None:
        await bot.say("No entries found for '{}'".format(collection))
    else:
        await bot.say(txt)


@commands.cooldown(rate=1, per=600, type=commands.BucketType.channel)
@bot.command(pass_context=True, hidden=True,
    brief='Send the welcome message to a specific channel',
    description='Send the welcome message to a specific channel')
async def welcome(ctx, channel=''):
    write_log(command_prefix + 'welcome ' + channel, ctx)
    # await bot.say("message content", embed=your_embed)
    # await bot.send_message(destination, welcome_txt, embed=your_embed)
    # await bot.send_message(ctx.message.channel, welcome_txt)
    if len(channel) == 0:
        await bot.say(welcome_txt)
        return

    dest_channel = get_channel_from_str(ctx.message.server, channel)
    if dest_channel is not None:
        await bot.send_message(dest_channel, welcome_txt)
    else:
        print('Could not find channel: #{}'.format(channel))
        await bot.say('Could not find channel: #{}'.format(channel))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True, brief='Get PSS stardate & Melbourne time',
             description='Get PSS stardate, as well as the day and time in Melbourne, Australia. ' +
             ' Gives the name of the Australian holiday, if it is a holiday in Australia.')
async def time(ctx):
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
    await bot.say(str_time)


# @commands.is_owner()
@commands.cooldown(rate=24, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True, hidden=True,
    brief='These are testing commands, usually for debugging purposes',
    description='These are testing commands, usually for debugging purposes')
async def testing(ctx, *, action=None):
    if action == 'refresh':
        write_log(command_prefix + 'testing refresh', ctx)
        tbl, rtbl = p.get_char_sheet(refresh=True)
        raw_text = mkt.load_item_design_raw(refresh=True)
        await bot.say('Refreshed')
    elif action == 'restart':
        write_log(command_prefix + 'testing restart', ctx)
        if str(ctx.message.author) == BOT_OWNER:
            await bot.say('Bot will restart')
            quit()
        else:
            await bot.say('Only the bot owner can restart this bot')
    elif action == 'ping':
        write_log(command_prefix + 'testing ping', ctx)
        await bot.say('Pong!')
    elif action == 'info':
        write_log(command_prefix + 'testing info', ctx)
        server = ctx.message.server
        author = ctx.message.author
        channel = ctx.message.channel
        txt = 'Server: {} (id={})\n'.format(server, server.id)
        txt += 'Message Author: {} (id={})\n'.format(author, author.id)
        txt += 'This Channel: {} (id={})\n'.format(channel, channel.id)
        txt += 'Default Channel: {}\n'.format(server.default_channel)
        txt += 'Discord.py version: {}'.format(discord.__version__)
        await bot.say(txt)
    await bot.delete_message(ctx.message)


@commands.cooldown(rate=1, per=60, type=commands.BucketType.channel)
@bot.command(pass_context=True, hidden=True, brief='Gives the version number of the bot',
    description='Gives the version number of the bot')
async def version(ctx):
    write_log(command_prefix + 'version', ctx)
    txt = 'Bot version is {}'.format(BOT_VERSION)
    await bot.say(txt)


@commands.cooldown(rate=1, per=60, type=commands.BucketType.channel)
@bot.command(pass_context=True, hidden=True, brief='Makes the bot say something',
    description='Makes the bot say something. Only the bot owner is allowed to ' +
                'use this command.')
async def say(ctx, *, text=None):
    write_log(command_prefix + 'say {}'.format(text), ctx)
    if text is None:
        return
    if str(ctx.message.author) == BOT_OWNER:
        await bot.say(txt)
    await bot.delete_message(ctx.message)


if __name__ == '__main__':
    # Running the Discord Bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
