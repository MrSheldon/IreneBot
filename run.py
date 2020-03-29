from module import Currency
from module import Twitter2
from module import ImageUploader
from module import Music
from module import DreamCatcher
from module import BlackJack
from module import Miscellaneous
from module import keys
from module import Cogs
from module import Youtube
from module import Games
from module import GroupMembers
from module import logger as log
from discord.ext import commands
import discord
import sqlite3
import threading

client = commands.Bot(command_prefix='%', case_insensitive=True)
path = 'module\currency.db'
DBconn = sqlite3.connect(path, check_same_thread=False)
c = DBconn.cursor()

path1 = 'module/GroupMembers.db'
DBconn1 = sqlite3.connect(path1, check_same_thread=False)
c1 = DBconn1.cursor()


def IreneBot():
    # events
    @client.event
    async def on_ready():
        await client.change_presence(status=discord.Status.online, activity=discord.Game("%help"))
        log.console('Irene is online')

    # Change this to the id of a channel you want the logged messages to go to
    # This can easily be changed into a database format; but I put it here because I know exactly where I want it
    # and logging is only meant for the bot owner anyway.
    # DO NOT FORGET THERE ARE 2 WAYS TO LOG
    # THERE IS ALREADY A LOGGING SYSTEM USING %logging
    # logging_channel_id is the main for the logging command
    logging_channel_id = 0
    # below is for private logging [can be used for certain text channels that you want logged but not others]
    logging_channel_id2 = 0

    @client.event
    async def on_message(message):
        try:
            # fetching temporary channels that have delays for removed messages.
            temp_channels = c.execute("SELECT chanID, delay FROM TempChannels").fetchall()
            # private takes channel IDs that are meant to be logged [Meant to be used for cross-server messages.]
            # this is the 2nd way to log
            private = c.execute("SELECT ChannelID FROM loggingprivate").fetchall()
            # This part was just to organize beforehand in case I wanted to use anything in the future
            message_sender = message.author
            message_content = message.clean_content
            message_channel = message.channel
            message_guild = message.guild
            message_created = message.created_at
            message_link = message.jump_url
            # check if messages are in a temporary channel
            for temp in temp_channels:
                chan_id = temp[0]
                delay = temp[1]
                if message_channel.id == chan_id:
                    await message.delete(delay=delay)
            # check if the message belongs to the bot
            if message_sender.id != client.user.id:
                if message_content[0] != '%':
                    # it had to be written somewhere :(
                    if 'nigga' in message_content.lower() or 'nigger' in message_content.lower():
                        author_id = message_sender.id
                        # checks how many instances ( should logically only be 0 or 1 )
                        checker = c.execute("SELECT COUNT(*) FROM Counter WHERE UserID = ?", (author_id,)).fetchone()[0]
                        if checker > 0:
                            current_count = c.execute("SELECT NWord FROM Counter WHERE UserID = ?", (author_id,)).fetchone()[0]
                            current_count += 1
                            c.execute("UPDATE Counter SET NWord = ? WHERE UserID = ?", (current_count, author_id))
                        if checker == 0:
                            current_count = 1
                            c.execute("INSERT INTO Counter VALUES (?,?)", (author_id, current_count))
                        DBconn.commit()
            # only log messages that are not commands
            if message_content[0] != '%':
                if message.author.id != client.user.id:
                    logging_channel = client.get_channel(logging_channel_id)
                    counter = c.execute("SELECT COUNT(*) FROM logging").fetchone()[0]
                    if counter > 0:
                        channels = c.execute("SELECT channelid FROM logging").fetchall()
                        for channel in channels:
                            channel = channel[0]
                            if channel == message.channel.id:
                                embed_message = f"**{message_sender}\nMessage: **{message_content}**\nFrom {message_guild} in {message_channel}\nCreated at {message_created}\n<{message_link}>**"
                                embed = discord.Embed(title="Log", description=embed_message, color=0xff00f6)
                                await logging_channel.send(embed=embed)
            # check the private list to see if it's specifically for a group of text channels.
            if message_channel.id in private:
                if message_content[0] != '%':
                    if message.author.id != client.user.id:
                        logging_channel = client.get_channel(logging_channel_id2)
                        embed_message = f"**{message_sender}\nMessage: **{message_content}**\nFrom {message_guild} in {message_channel}\nCreated at {message_created}\n<{message_link}>**"
                        embed = discord.Embed(title="Log", description=embed_message, color=0xff00f6)
                        await logging_channel.send(embed=embed)
            if message_content[0] == '%':
                log.console(f"COMMAND LOG: {message_sender} || {message_content} ")
        except Exception as e:
            # log.console(e)
            pass
        await client.process_commands(message)

    @client.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            pass
        if isinstance(error, commands.errors.CommandInvokeError):
            log.console(f"Command Invoke Error -- {error}")
            pass
        if isinstance(error, commands.errors.CommandOnCooldown):
            embed = discord.Embed(title="Error", description=f"** {error} **", color=0xff00f6)
            await ctx.send(embed=embed)
            log.console(f"{error}")
            pass
        if isinstance(error, commands.errors.BadArgument):
                embed = discord.Embed(title="Error", description=f"** {error} **", color=0xff00f6)
                await ctx.send(embed=embed)
                log.console(f"{error}")
                ctx.command.reset_cooldown(ctx)
                pass
    # Start Automatic DC Loop
    DreamCatcher.DCAPP().new_task4.start()
    # Start Automatic Youtube Scrape Loop
    Youtube.YoutubeLoop().new_task5.start()

    Miscellaneous.setup(client)
    Music.setup(client)
    ImageUploader.setup(client)
    Twitter2.setup(client)
    Currency.setup(client)
    DreamCatcher.setup(client)
    BlackJack.setup(client)
    Cogs.setup(client)
    Youtube.setup(client)
    Games.setup(client)
    client.add_listener(GroupMembers.on_message2, 'on_message')
    GroupMembers.setup(client)

    # start logging console and file
    # For INFO Logging
    log.info()
    # For Debugging
    # log.debug()

    # run bot
    client.run(keys.client_token)


# Threads created in case needed for future

t1 = threading.Thread(target=IreneBot)
t1.start()


