from discord.ext import commands, tasks
import sqlite3
import aiohttp
from bs4 import BeautifulSoup as soup
from datetime import *

client = 0
path = 'module\currency.db'
DBconn = sqlite3.connect(path, check_same_thread=False)
c = DBconn.cursor()

def setup(client1):
    client1.add_cog(Youtube(client1))
    global client
    client = client1


class Youtube(commands.Cog):
    def __init__(self, client):
        pass

    @commands.command()
    @commands.is_owner()
    async def addurl(self, ctx, link):
        """Add url to youtube videos [Format: %addurl (link)]"""
        if 'youtube.com' in link or 'youtu.be' in link:
            try:
                c.execute("INSERT INTO Links VALUES(NULL,?)", (link,))
                DBconn.commit()
                await ctx.send("> **That video is now being traced**")
            except Exception as e:
                print (e)
                await ctx.send("> **That video is already being tracked.**")

    @commands.command()
    @commands.is_owner()
    async def removeurl(self, ctx, link):
        """Remove url from youtube videos [Format: %removeurl (link)]"""
        try:
            c.execute("DELETE FROM Links WHERE Link = ?", (link,))
            DBconn.commit()
            await ctx.send("> **That video has been deleted**")
        except:
            await ctx.send("> **That video is not being tracked.**")
    # this is the equivalent of the loop, but without actually looping. It only does it once and sends message to a channel.
    @commands.command()
    @commands.is_owner()
    async def scrapeyoutube(self, ctx):
        """Scrape Youtube Video"""
        links = c.execute("SELECT Link FROM links").fetchall()
        for link in links:
            id = c.execute("SELECT LinkID FROM links WHERE Link = ?", (link,)).fetchone()[0]
            async with aiohttp.ClientSession() as session:
                async with session.get('{}'.format(link[0])) as r:
                    if r.status == 200:
                        page_html = await r.text()
                        print(page_html)
                        page_soup = soup(page_html, "html.parser")
                        view_count = (page_soup.find("div", {"class": "watch-view-count"})).text
                        # c.execute("INSERT INTO ViewCount VALUES (?,?)", (id,datetime.now()))
                        await ctx.send(f"> **Managed to scrape Video Name -- {view_count} -- {datetime.now()}**")

    @commands.command()
    @commands.is_owner()
    async def stoploop(self, ctx):
        """Stops scraping youtube videos [Format: %stoploop]"""
        YoutubeLoop().new_task5.stop()
        await ctx.send("> **If there was a loop, it stopped.**")

    @commands.command()
    @commands.is_owner()
    async def startloop(self, ctx):
        """Starts scraping youtube videos [Format: %startloop]"""
        try:
            YoutubeLoop().new_task5.start()
            await ctx.send("> **Loop started.**")
        except:
            await ctx.send("> **A loop is already running.**")


class YoutubeLoop:
    def __init__(self):
        self.view_count = []
        self.now = []
        pass
    # loop set to 30 minutes
    @tasks.loop(seconds=0, minutes=30, hours=0, reconnect=True)
    async def new_task5(self):
        try:
            links = c.execute("SELECT Link FROM links").fetchall()
            for link in links:
                link_id = c.execute("SELECT LinkID FROM links WHERE Link = ?", (link)).fetchone()[0]
                async with aiohttp.ClientSession() as session:
                    async with session.get('{}'.format(link[0])) as r:
                        if r.status == 200:
                            page_html = await r.text()
                            # print(page_html)
                            page_soup = soup(page_html, "html.parser")
                            view_count = (page_soup.find("div", {"class": "watch-view-count"})).text
                            now = datetime.now()
                            c.execute("INSERT INTO ViewCount VALUES (?,?,?)", (link_id, view_count, now))
                            self.view_count.append(view_count)
                            self.now.append(now)
                            DBconn.commit()
            print("Updated Video Views Tracker")
        except Exception as e:
            print(e)
        channel = client.get_channel(679553820648538269)
        # Below is code I used for sending to a channel (which was why I made self variables)
        # There were errors with the channel not being found and I needed to get it done asap, so I went this route
        """
        for i in range (len(self.view_count)):
            if i % 2 == 0:
                await channel.send(f">>> ** Video Name - {self.view_count[i]} - {self.now[i]} EST\n**")
            else:
                await channel.send(f">>> ** Video Name - {self.view_count[i]} - {self.now[i]} EST\n**")
        self.view_count = []
        self.now = []
        """