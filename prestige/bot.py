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
import time, datetime


# ----- Setup ---------------------------------------------------------
command_prefix = os.getenv('COMMAND_PREFIX')
tbl, rtbl = p.get_char_sheet()


# ----- Utilities -----------------------------------------------------
def write_log(log_text, ctx=None):
    time_text = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    ctx_text = '' if ctx is None else \
        '{}@{}'.format(ctx.message.author, ctx.message.server)

    final_text = '{} {}: {}'.format(time_text, ctx_text, log_text)
    with open("discord-bot.log", "a") as f:
        f.write(final_text + '\n')
    print(final_text)


# ----- Bot -----------------------------------------------------------
logging.basicConfig(level=logging.INFO)
bot = commands.Bot(description='This is a bot for pixel starships',
    command_prefix=command_prefix)


@bot.event
async def on_ready():
    write_log('Hi, bot logged in as {}'.format(bot.user.name))


@bot.command()
async def ping():
    await bot.say('Pong!')


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


@bot.command(pass_context=True)
async def market(ctx):
    market_txt = mkt.get_market_data()
    try:
        await bot.say(market_txt)
    except:
        write_log('Failed to send the following to bot')
        write_log('"{}"'.format(market_txt))


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


@bot.command(pass_context=True)
async def refresh():
    write_log(command_prefix + 'refresh', None)
    tbl, rtbl = p.get_char_sheet(refresh=True)
    await bot.say('Refreshed')


if __name__ == '__main__':
    # Running the Discord Bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
