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
import time, datetime


# ----- Setup ---------------------------------------------------------
tbl, rtbl = p.get_char_sheet()


# ----- Utilities -----------------------------------------------------
def write_log(log_text, ctx=None):
    time_text = datetime.datetime.now().time().strftime('%H:%M:%S')
    ctx_text = '' if ctx is None else \
        "{}@{}".format(ctx.message.author, ctx.message.server)

    final_text = '{} {}: {}'.format(time_text, ctx_text, log_text)
    with open("discord-bot.log", "a") as f:
        f.write(final_text + '\n')
    print(final_text)


# ----- Bot -----------------------------------------------------------
logging.basicConfig(level=logging.INFO)
bot = commands.Bot(description="This is a bot for pixel starships",
    command_prefix='/')


@bot.event
async def on_ready():
    write_log("Hi, bot logged in as {}".format(bot.user.name))


@bot.command()
async def ping():
    await bot.say("Pong!")


@bot.command(pass_context=True)
async def prestige(ctx, *, char_name=None):
    if char_name is None:
        await bot.say("Enter: ?prestige [character name]")
    else:
        write_log("?prestige {}".format(char_name), ctx)
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
        await bot.say("Enter: ?recipe [character name]")
    else:
        write_log("?recipe {}".format(char_name), ctx)
        content, ptbl = p.get_prestige_data(char_name, 'to', rtbl)
        if content is None:
            await bot.say("Could not find {}".format(char_name))
        else:
            prestige_text = p.get_prestige_text(ptbl, tbl, 'to')
            try:
                for txt in prestige_text:
                    await bot.say(txt)
            except:
                write_log('Failed to send the following to bot')
                write_log('"{}"'.format(prestige_text))


@bot.command(pass_context=True)
async def refresh():
    write_log("?refresh", None)
    tbl, rtbl = p.get_char_sheet(refresh=True)
    await bot.say("Refreshed")


if __name__ == "__main__":
    # Running the Discord Bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.run(token)
