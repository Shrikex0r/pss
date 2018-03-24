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
import pss_prestige as p
import pss_market as mkt
import pytz
import time, datetime


# ----- Setup ---------------------------------------------------------
command_prefix = os.getenv('COMMAND_PREFIX')
BOT_OWNER = os.getenv("DISCORD_BOT_OWNER")

tbl, rtbl = p.get_char_sheet()
# welcome_txt = """**Welcome to the Pixel Starships Discord!**
# This is a place where we can interact with devs and players from other alliances/fleets
# 1. :zipper_mouth: you can mute any channel to avoid notifications from that channel
# 2. :microphone: #announcements-and-tips-of-the-day are for anything really important on PSS, as well as a means for the devs to post announcements
# 3. :bulb: if you have any suggestions for the game, you can post them in #suggestion-posts. previously discussed suggestions are in #summaries
# 4. :beetle: #game-support is for bugs, etc. \@@TheRealTiffany is usually there
# 5. :robot: We have a #dolores-bot-room. type “`/help`” to find out how to use the bot for character stats/prestige combos, and item prices/stats.
# 6. :art: Get a Discord color by posting a screenshot with your trophy level in #screenshots
# 7. :dove: The usual guidelines for any forum apply (try to be civil, don’t spam, etc)."""
welcome_txt = """**Welcome to the Pixel Starships Discord!**
This is a place where we can interact with devs and players from other alliances/fleets
1. 🤐 you can mute any channel to avoid notifications from that channel
2. 🎤 #announcements-and-tips-of-the-day are for anything really important on PSS, as well as a means for the devs to post announcements
3. 💡 if you have any suggestions for the game, you can post them in #suggestion-posts. previously discussed suggestions are in #summaries
4. 🐞 #game-support is for bugs, etc. \@@TheRealTiffany is usually there
5. 🤖 We have a #dolores-bot-room. type “`/help`” to find out how to use the bot for character stats/prestige combos, and item prices/stats.
6. 🎨 Get a Discord color by posting a screenshot with your trophy level in #screenshots
7. 🕊 The usual guidelines for any forum apply (try to be civil, don’t spam, etc)."""

# ----- Utilities -----------------------------------------------------
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


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command()
async def ping():
    await bot.say('Pong!')


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True)
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
@bot.command(pass_context=True)
async def recipe(ctx, *, char_name=None):
    if char_name is None:
        help_txt = 'Enter: {}recipe [character name]'.format(command_prefix)
        await bot.say(help_txt)
    else:
        write_log(command_prefix + 'recipe {}'.format(char_name), ctx)
        content, ptbl = p.get_prestige_data(char_name, 'to', rtbl)
        if content is None:
            await bot.say('Could not find {}'.format(char_name))
        else:
            prestige_text = p.get_prestige_text(ptbl, tbl, 'to')
            try:
                for txt in prestige_text:
                    await bot.say(txt)
            except:
                write_log('Failed to send the following to bot')
                write_log('"{}"'.format(prestige_text))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True)
async def market(ctx):
    market_txt = mkt.get_market_data()
    try:
        await bot.say(market_txt)
    except:
        write_log('Failed to send the following to bot')
        write_log('"{}"'.format(market_txt))


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True)
async def price(ctx, *, item_name=None):
    if item_name is None:
        await bot.say('Enter: {}price [item name]'.format(command_prefix))
    else:
        write_log(command_prefix + 'price {}'.format(item_name), ctx)
        raw_text = mkt.load_item_design_raw()
        rtbl = mkt.parse_item_designs(raw_text)
        market_txt = mkt.filter_item_designs(item_name, rtbl, filter='price')
        if market_txt is None:
            await bot.say('Could not find {}'.format(item_name))
        else:
            await bot.say(market_txt)


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True)
async def stats(ctx, *, name=None):
    if name is None:
        await bot.say('Enter: {}stats [name]'.format(command_prefix))
        return

    write_log(command_prefix + 'stats {}'.format(name), ctx)
    result = p.get_stats(name, embed=False)
    if result is None:
        await bot.say('Could not find {}'.format(name))
    else:
        await bot.say(result)


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True)
async def item(ctx, *, name=None):
    if name is None:
        await bot.say('Enter: {}item [name]'.format(command_prefix))
        return

    write_log(command_prefix + 'item {}'.format(name), ctx)
    raw_text = mkt.load_item_design_raw()
    rtbl = mkt.parse_item_designs(raw_text)
    market_txt = mkt.filter_item_designs(name, rtbl, filter='stats')
    if market_txt is None:
        await bot.say('Could not find {}'.format(name))
    else:
        await bot.say(market_txt)


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
@bot.command(pass_context=True)
async def best(ctx, slot=None, enhancement=None):
    if slot is None:
        txt = 'Enter: {}best [slot] [enhancement]'.format(command_prefix)
        await bot.say(txt)
        return
    txt = command_prefix + 'best {} {}'.format(slot, enhancement)
    write_log(txt, ctx)

    raw_text = mkt.load_item_design_raw()
    rtbl = mkt.parse_item_designs(raw_text)
    df_items = mkt.rtbl2items(rtbl)
    df_filter = mkt.filter_item(
        df_items, slot, enhancement,
        cols=['ItemDesignName', 'EnhancementValue'])

    txt = mkt.itemfilter2txt(df_filter)
    if txt is None:
        await bot.say('No entries found for {} slot, {} enhancement'.format(
            slot, enhancement))
    else:
        await bot.say(txt)


def get_channel_from_str(server, channel_str):
    for i, channel in enumerate(server.channels):
        # txt += '{}: Channel: {} (id={})'.format(i, channel.name, channel.id)
        if channel.name == channel_str:
            return channel
    return None


@commands.cooldown(rate=1, per=600, type=commands.BucketType.channel)
@bot.command(pass_context=True, hidden=True)
async def welcome(ctx):
    write_log(command_prefix + 'welcome', ctx)
    # await bot.say("message content", embed=your_embed)
    # await bot.send_message(destination, welcome_txt, embed=your_embed)
    # await bot.send_message(ctx.message.channel, welcome_txt)
    dest_channel = get_channel_from_str(ctx.message.server, 'general')
    if dest_channel is not None:
        await bot.send_message(dest_channel, welcome_txt)
    else:
        print('Could not find channel: #general')


@commands.cooldown(rate=12, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True)
async def time(ctx):
    mel_tz = pytz.timezone('Australia/Melbourne')
    now = datetime.datetime.now()
    mel_time = now.replace(tzinfo=pytz.utc).astimezone(mel_tz)
    str_time = 'Time in Melbourne: {}'.format(mel_time.strftime('%H:%M'))
    await bot.say(str_time)


@commands.cooldown(rate=24, per=120, type=commands.BucketType.channel)
@bot.command(pass_context=True, hidden=True)
async def testing(ctx, *, action=None):
    if action == 'refresh':
        write_log(command_prefix + 'testing refresh', ctx)
        tbl, rtbl = p.get_char_sheet(refresh=True)
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
        txt = 'Server: {}\n'.format(server)
        txt += 'Message Author: {}\n'.format(ctx.message.author)
        txt += 'This Channel: {}\n'.format(ctx.message.channel)
        txt += 'Default Channel: {}\n'.format(server.default_channel)
        await bot.say(txt)


if __name__ == '__main__':
    # Running the Discord Bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
