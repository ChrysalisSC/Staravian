"""
Python Bot V2

Description:
This Python script serves as a template for creating a bot application. It can be used as a foundation for building various types of bots, such as chatbots, automation bots, or social media bots.

Author: Colton Trebbien
Date: 04/08/2024

Dependencies:
- [List of Python modules/libraries required]

Usage:
- [Instructions on how to use the bot, including any command-line arguments or configuration settings]

Notes:
- [Any additional notes or considerations for using the bot]
"""

# IMPORTS
import os
import json
import sys
import pytz
import datetime
import time


from backend.common.common import log


import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import app_commands


from dotenv import load_dotenv
load_dotenv()

from backend.utilities.users import *
from backend.utilities.renown import *

from backend.cogs.general.central import Central, setup as setup_central

from backend.cogs.level import levelup
from backend.cogs.example_cog import MyCog
from backend.cogs.music.kpop import Kpop
from backend.cogs.music.kpop import setup as setup_kpop
from backend.cogs.level import setup as setup_level
from backend.cogs.games.server_games.wordle import Wordle
from backend.cogs.games.server_games.wordle import setup as setup_wordle
from backend.cogs.threads import ThreadManager
from backend.cogs.threads import setup as setup_threads
from backend.cogs.games.server_games.fish import Fish
from backend.cogs.games.server_games.fish import setup as setup_fish
from backend.cogs.user import Users
from backend.cogs.user import setup as setup_users
from backend.cogs.shop import Shop
from backend.cogs.shop import setup as setup_shop
from backend.cogs.tavern import Tavern
from backend.cogs.tavern import setup as setup_tavern
from backend.cogs.supply_drops import RewardCog
from backend.cogs.supply_drops import setup as setup_supply_drops
from backend.cogs.games.server_games.games import Games
from backend.cogs.games.server_games.games import setup as setup_games
from backend.cogs.general.random_announcements import Announcement
from backend.cogs.general.random_announcements import setup as setup_announcement

CONFIG = None
MIDNIGHT = datetime.time(hour=19, minute=11, second=0, microsecond=0)
pst = pytz.timezone('America/Los_Angeles')
# Create a time object representing 6:07 PST
#MIDNIGHT = datetime.time(hour=6, minute=7, second=0, microsecond=0, tzinfo=pst)
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

script_dir = os.path.dirname(os.path.abspath(__file__)) #this is main
parent_dir = os.path.dirname(script_dir) # this is 


def get_pacific_time():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    pacific_now = utc_now.astimezone(pytz.timezone('America/Los_Angeles'))
    return pacific_now

def load_config(env):
    # Define the path to the configuration file based on the environment
    global CONFIG
    # Get the directory where the script is located

    config_file =  f'config/{env}.json'
   

    # Check if the configuration file exists
    if os.path.exists(config_file):
        # Load and parse the configuration file
        with open(config_file, 'r') as f:
            CONFIG = json.load(f)
            f.close()
        # check if the config fild has the correct keys
        keys = ["Version", "ENVIRONMENT", "DISCORD_API", "GUILD_ID", "KPOP_ID", "FISH_ID", "LEVEL_ID", "SHOP_ID", "TAVERN_ID", "POP_ID", "REWARD_ID", "GAMES_ID", "MUSIC_ROLE"]
        for key in keys:
            if key not in CONFIG:
                print(f"Configuration file '{config_file}' is missing the key '{key}'.")
                return None
            
        return CONFIG
    else:
        print(f"Configuration file '{config_file}' not found.")
        return None
    
@bot.command()
async def sync(ctx):
    try:
        G = bot.get_guild(int(CONFIG['GUILD_ID']))
        bot.tree.copy_global_to(guild=G)
        synced = await bot.tree.sync(guild=G)
      
        await ctx.send(f"Synced {len(synced)} command(s).")
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        await ctx.send(f"Error syncing commands: {e}")
        print(f"Error syncing commands: {e}")


async def delete_all_threads():
    # Iterate over each guild the bot is connected to
    for guild in bot.guilds:
        # Iterate over each channel in the guild
        for channel in guild.text_channels:
            # Fetch the threads in the channel
            threads = channel.threads
            # Delete each thread
            for thread in threads:
                await thread.delete()

@bot.event
async def on_message(message):
    # Ensure the message is not sent by the bot itself
    #check to make sure the user database is created inside the databases fold
  
    if not os.path.exists("backend/databases/user_data.db"):
        log("MAIN", "User Database not found, Run !setup_bot to create it")
        await bot.process_commands(message)
        return


    time = str(get_pacific_time())
    if message.author == bot.user:
        return
    if message.author.bot:
        return
    try:
        log("MAIN", f"{message.author} - {message.content}")
    except:
        log("MAIN", f"{message.author} - ERROR MESSAGE")
    try:
        await add_xp(bot, message.author.id, 50, 'XP')
        print("added xp")
        update_last_seen( message.author.id, time)
        print("updated last seen")
        await add_renown_to_user(bot, message.author.id, 50,  await get_selected_track(message.author.id))
        print("added renown")
        pass
    except:
        pass
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    # Define the welcome embed
    print()

    embed = discord.Embed(
        title=f"Welcome to the server, {member.name}!",
        description="We are excited to have you here.",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar)
    embed.add_field(name="Rules", value="Be respectful and follow the server rules.")
    embed.set_footer(text=f"Joined at {member.joined_at}")
    
    # Send the embed to a specific channel (replace 'welcome_channel_id' with your channel ID)
    welcome_channel = bot.get_channel(1253800012630986854)
    if welcome_channel:
        await welcome_channel.send(embed=embed)

@tasks.loop(minutes=1)
async def background_task():
    time = str(get_pacific_time())
    for guild in bot.guilds:
        for member in guild.members:
            if member.voice and member.voice.channel:
                await add_xp(bot, member.id, 1, 'XP')
                await add_renown_to_user(bot, member.id, 1, "level")
                add_time_to_user(member.id, 60)
                update_last_seen(member.id, time)
                #await add_renown_to_user(bot, member.id, 1, "resonance")
                track = await get_selected_track(member.id)
                # if track is none, dont add to it
                if track:
                    await add_renown_to_user(bot, member.id, 1, track)



#@tasks.loop(time=[MIDNIGHT])    
#@tasks.loop(minutes=1)
@tasks.loop(time=[MIDNIGHT])   
async def daily_reset():
    update_ranks()
    shop_cog_instance = bot.get_cog("Shop")
    await shop_cog_instance.shop()

async def add_users_to_db():
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:  # Skip bot accounts
                print(f"Adding user {member.id} - {member}")
                #if user doesnt esist in db, add them
                add_user(member.id, str(member))
                #add novice role to user
                
@bot.event
async def on_ready():
    log("CENTRAL COMMAND", "Logged in as Star Bot")

    # Add the cogs to the bot
    await delete_all_threads()
    await setup_central(bot, CONFIG) #CENTRAL NEEDS TO RUN FIRST ALWAYS
    await setup_threads(bot,CONFIG)
    await setup_users(bot, CONFIG)
    await setup_tavern(bot, CONFIG)
    await setup_games(bot, CONFIG)
    await setup_kpop(bot, CONFIG)
    await setup_shop(bot, CONFIG)
    await setup_level(bot, CONFIG)
    #await setup_supply_drops(bot, CONFIG)
    #await setup_announcement(bot, CONFIG)

    daily_reset.start()
    #await setup_wordle(bot, CONFIG)
    #await setup_fish(bot, CONFIG)
    #await setup_shop(bot, CONFIG)
    #await setup_tavern(bot, CONFIG)
    #await setup_supply_drops(bot, CONFIG)
    #await setup_games(bot, CONFIG)
    #await setup_announcement(bot, CONFIG)
    #await create_table()  # Ensure the USERDATA table is created when the bot starts

    central_cog = bot.get_cog("Central")
    if central_cog:
        await central_cog.load_views()

    #background_task.start()
   
   

    #create_table_renown()
    #await daily_reset.start()
    log("CENTRAL COMMAND", "Bot is Running Successfully")

if __name__ == "__main__":
    # Check if the environment is provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python main.py <env>")
        sys.exit(1)

    # Get the environment from the command-line argument
    env = sys.argv[1]
    log("CENTRAL COMMAND", f"Starting bot in {env} environment")
    # Load the configuration based on the provided environment
    load_config(env)
    if CONFIG:
        print("Configuration loaded successfully")
        bot.run(str(CONFIG['DISCORD_API']))
    else:
        print("Failed to load configuration.")
    
  
