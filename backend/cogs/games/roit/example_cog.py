import discord
from discord.ext import commands
from discord import app_commands

from backend.common.common import log

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """A simple command that says hello"""
        log("[EXAMPLE]", "HELLO")
        await ctx.send('Hello!')

    @commands.Cog.listener()
    async def on_ready(self):
        """Event listener that runs when the bot is ready"""
        print(f'{self.bot.user} has connected to Discord!')

async def setup(bot, config):
    #name of your log(name of cog, print_info)
    log("EXAMPLE", "Setting up Example cog...")
    await bot.add_cog(MyCog(bot, config))
   

