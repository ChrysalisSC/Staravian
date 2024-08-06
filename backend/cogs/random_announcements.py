import discord
from discord.ext import commands
from discord import app_commands

from common import log
import json

class Announcement(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot

    @commands.command()
    async def world_track(self, ctx):
        embed = discord.Embed(
            title="World Track",
            description="The World Track is a track that rewards users for participating in the community. The more active you are, the more rewards you will earn!",
            color=discord.Color.blue()
        )
        with open ("shared_config/world.json", "r") as file:
            rewards = json.load(file)
     

        rewards_part1 = []
        rewards_part2 = []

        for i, (level, reward) in enumerate(rewards.items(), 1):
            details = f"Credits: {reward['credits']}\n"

            if 'title' in reward:
                details += f"Title: {reward['title']}\n"
            if 'color' in reward:
                details += f"Color: {reward['color']}\n"
            if 'header' in reward:
                details += f"Header: {reward['header']}\n"
            if 'background' in reward:
                details += f"Background: {reward['background']}\n"
            if 'buff' in reward:
                details += f"Buff: {reward['buff']}\n"
            if 'badge' in reward:
                details += f"Badge: {reward['badge']}\n"

            # Determine which part (list) to add the reward to
            if i <= 11:
                rewards_part1.append(f"{level} - {details}")
            else:
                rewards_part2.append(f"{level} - {details}")

        # Join the rewards lists with newlines for formatting
        rewards_part1_formatted = "\n".join(rewards_part1)
        rewards_part2_formatted = "\n".join(rewards_part2)

        embed.add_field(name="", value=rewards_part1_formatted, inline=True)
        embed.add_field(name="", value=rewards_part2_formatted, inline=True)

         
        await ctx.send(embed=embed)
    
    @commands.command()
    async def renown_track(self, ctx):
        embed = discord.Embed(
            title="Renown Track",
            description="The Renown Track is a track that rewards users for participating in the community. The more active you are, the more rewards you will earn!",
            color=discord.Color.blue()
        )
    
 


async def setup(bot, config):
    #name of your log(name of cog, print_info)
    log("ANNONCE", "Setting up Example cog...")
    await bot.add_cog(Announcement(bot, config))
   
