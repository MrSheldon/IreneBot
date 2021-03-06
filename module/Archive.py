import discord
import os
from discord.ext import commands
import aiohttp
import aiofiles
import asyncio
from module import logger as log
from random import *
from datetime import datetime
from Utility import DBconn, c, fetch_one, fetch_all


class Archive(commands.Cog):
    def __init__(self, client):
        client.add_listener(self.on_message, 'on_message')
        self.client = client
        self.bot_owner_id = 0
        pass

    async def on_message(self, message, owner=0):
        if owner == 1:
            try:
                def check(m):
                    return m.channel == message.channel and m.author.id == self.bot_owner_id

                msg = await self.client.wait_for('message', timeout=60, check=check)
                if msg.content.lower() == "confirm" or msg.content.lower() == "confirmed":
                    return True
            except asyncio.TimeoutError:
                return False

        if owner == 0:
            if not message.author.bot:
                try:
                    c.execute("SELECT id, channelid, guildid, driveid, name FROM archive.channellist")
                    all_channels = fetch_all()
                    for channel in all_channels:
                        ID = channel[0]
                        ChannelID = channel[1]
                        GuildID = channel[2]
                        drive_id = channel[3]
                        Name = channel[4]
                        if message.channel.id == ChannelID:
                            if len(message.attachments) > 0:
                                for file in message.attachments:
                                    url = file.url
                                    if "%27%3E" in url:
                                        pos = url.find("%27%3E")
                                        url = url[0:pos - 1]
                                    if ":large" in url:
                                        pos = url.find(":large")
                                        url = url[0:pos]
                                    await self.download_url(url, drive_id, message.channel.id)
                                # quickstart.Drive.checker()
                            if len(message.embeds) > 0:
                                for embed in message.embeds:
                                    if str(embed.url) == "Embed.Empty":
                                        pass
                                    else:
                                        url = embed.url
                                        if "%27%3E" in url:
                                            pos = url.find("%27%3E")
                                            url = url[0:pos-1]
                                        if ":large" in url:
                                            pos = url.find(":large")
                                            url = url[0:pos]
                                        await self.download_url(url, drive_id, message.channel.id)
                                    # quickstart.Drive.checker()
                            await self.deletephotos()
                except Exception as e:
                    # log.console(e)
                    pass

    @commands.has_guild_permissions(manage_messages=True)
    @commands.command()
    async def addchannel(self, ctx, drive_folder_id, name="NULL", owner_present=0):
        """REQUIRES BOT OWNER PRESENCE -- Make the current channel start archiving images to google drive [Format: %addchannel <drive folder id> <optional - name>]"""
        try:
            if owner_present == 0:
                await ctx.send(f"> **In order to start archiving your channels, you must talk to the bot owner <@{self.bot_owner_id}>**")
            if owner_present == 1:
                await ctx.send("> **Awaiting confirmation**")
                if await self.on_message(ctx, 1):
                    c.execute("SELECT COUNT(*) FROM archive.ChannelList WHERE DriveID = %s", (drive_folder_id,))
                    checker = fetch_one()
                    if checker == 0:
                        c.execute("SELECT COUNT(*) FROM archive.ChannelList WHERE ChannelID = %s", (ctx.channel.id,))
                        count = fetch_one()
                        if count == 0:
                            url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
                            async with aiohttp.ClientSession() as session:
                                async with session.get(url) as r:
                                    if r.status == 200:
                                        c.execute("INSERT INTO archive.ChannelList VALUES(%s,%s,%s,%s)", (ctx.channel.id, ctx.guild.id, drive_folder_id, name))
                                        DBconn.commit()
                                        await ctx.send(f"> **This channel is now being archived under {url}**")
                                        pass
                                    elif r.status == 404:
                                        await ctx.send(f"> **{url} does not exist.**")
                                    elif r.status == 403:
                                        await ctx.send(f"> **I do not have access to {url}.**")
                                    else:
                                        await ctx.send(f"> **Something went wrong with {url}")
                        else:
                            await ctx.send("> **This channel is already being archived**")
                    else:
                        url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
                        await ctx.send(f"> **{url} is already being used.**")
                else:
                    await ctx.send("> **The bot owner did not confirm in time.**")
        except Exception as e:
            log.console(e)
            await ctx.send("> **There was an error.**")
        pass

    @commands.has_guild_permissions(manage_messages=True)
    @commands.command()
    async def listchannels(self, ctx):
        """List the channels in your server that are being archived. [Format: %listchannels]"""
        c.execute("SELECT id, channelid, guildid, driveid, name FROM archive.ChannelList")
        all_channels = fetch_all()
        guild_name = ctx.guild.name
        embed = discord.Embed(title=f"Archived {guild_name} Channels", color=0x87CEEB)
        embed.set_author(name="Irene", url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', icon_url='https://cdn.discordapp.com/emojis/693392862611767336.gif?v=1')
        embed.set_footer(text="Thanks for using Irene.", icon_url='https://cdn.discordapp.com/emojis/683932986818822174.gif?v=1')
        check = False
        for channel in all_channels:
            ID = channel[0]
            ChannelID = channel[1]
            list_channel = (await self.client.fetch_channel(ChannelID)).name
            GuildID = channel[2]
            DriveID = channel[3]
            Name = channel[4]
            if ctx.guild.id == GuildID:
                check = True
                embed.insert_field_at(0, name=list_channel, value=f"https://drive.google.com/drive/folders/{DriveID} | {Name}", inline=False)
                pass
        if check:
            await ctx.send(embed=embed)
        else:
            await ctx.send("> **There are no archived channels on this server.**")

    @commands.has_guild_permissions(manage_messages=True)
    @commands.command()
    async def deletechannel(self, ctx):
        """Stop the current channel from being archived [Format: %deletechannel]"""
        try:
            c.execute("SELECT COUNT(*) FROM archive.ChannelList WHERE ChannelID = %s", (ctx.channel.id,))
            count = fetch_one()
            if count == 0:
                await ctx.send("> **This channel is not currently being archived.**")
            else:
                c.execute("DELETE FROM archive.ChannelList WHERE ChannelID = %s", (ctx.channel.id,))
                DBconn.commit()
                await ctx.send("> **This channel is no longer being archived**")
        except Exception as e:
            log.console(e)
            await ctx.send("> **There was an error.**")

    async def download_url(self, url, drive_id, channel_id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    check = False
                    if r.status == 200:
                        unique_id = randint(0, 1000000000000)
                        unique_id2 = randint(0, 1000)
                        unique_id3 = randint(0, 500)
                        src = url[len(url)-4:len(url)]
                        checkerx = url.find(":large")
                        if checkerx != -1:
                            src = url[len(url)-10:len(url)-6]
                            url = f"{url[0:checkerx-1]}:orig"

                        src2 = url.find('?format=')
                        if src2 != -1:
                            check = True
                            src = f".{url[src2+8:src2+11]}"
                            url = f"{url[0:src2-1]}{src}:orig"
                        if src == ".jpg" or src == ".gif" or src == '.png' or check:
                            file_name = f"1_{unique_id}_{unique_id2}_{unique_id3}{src}"
                            fd = await aiofiles.open(
                                'Photos/{}'.format(file_name), mode='wb')
                            await fd.write(await r.read())
                            await fd.close()
                            c.execute("INSERT INTO archive.ArchivedChannels VALUES(%s,%s,%s,%s)", (file_name, src, drive_id, channel_id))
                            DBconn.commit()
                        # quickstart.Drive.checker()
        except Exception as e:
            log.console(e)
            pass

    async def deletephotos(self):
        c.execute("SELECT FileName from archive.ArchivedChannels")
        allfiles = fetch_all()
        file_list = []
        for file in allfiles:
            file_list.append(file[0])
        all_photos = os.listdir('Photos')
        for photo in all_photos:
            if photo != "placeholder.txt" and photo not in file_list:
                try:
                    os.unlink('Photos/{}'.format(photo))
                except Exception as e:
                    pass

    @commands.has_guild_permissions(manage_messages=True)
    @commands.command()
    async def addhistory(self, ctx, year: int = None, month: int = None, day: int = None):
        """Add all of the previous images from a text channel to google drive."""
        if (year and month and day) is not None:
            after = datetime(year, month, day)
        else:
            after = None

        async def history(guild_id, drive_id):
            try:
                async for message in ctx.channel.history(limit=None, after=after):
                    if len(message.attachments) > 0:
                        for file in message.attachments:
                            url = file.url
                            if "%27%3E" in url:
                                pos = url.find("%27%3E")
                                url = url[0:pos - 1]
                            if ":large" in url:
                                pos = url.find(":large")
                                url = url[0:pos - 1]
                            await self.download_url(url, drive_id, ctx.channel.id)

                    if len(message.embeds) > 0:
                        for embed in message.embeds:
                            if str(embed.url) == "Embed.Empty":
                                pass
                            else:
                                url = embed.url
                                if "%27%3E" in url:
                                    pos = url.find("%27%3E")
                                    url = url[0:pos-1]
                                if ":large" in url:
                                    pos = url.find(":large")
                                    url = url[0:pos-1]
                                await self.download_url(url, drive_id, ctx.channel.id)

                    pass
            except Exception as e:
                log.console(e)
                pass
        check = False
        c.execute("SELECT channelid, guildid, driveid FROM archive.ChannelList")
        channels = fetch_all()
        for channel in channels:
            ChannelID = channel[0]
            GuildID = channel[1]
            DriveID = channel[2]
            if ctx.channel.id == ChannelID:
                check = True
                await ctx.send("> **Starting to check history... to prevent bot lag, an external program uploads them every 60 seconds.**")
                await history(GuildID, DriveID)
                await self.deletephotos()
                await ctx.send("> **Successfully added history of this text channel. They will be uploaded shortly.**")
        if not check:
            await ctx.send("> **This channel is not currently being archived.**")
