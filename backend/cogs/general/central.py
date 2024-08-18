import json
import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

from backend.common.common import log, get_time

from backend.utilities.database_setup import database_setup
from backend.utilities.users import add_user

from typing import Callable, Dict


class Central(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.view_creators = {}

    @commands.command()
    async def setup_bot(self, ctx):
        """
        Setup the bot by creating the databases and setting up the backend.
        """
        log("[CENTRAL]", "INITIALIZING BOT SETUP")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir) # this is the cog file's parent directory
        backend_dir = os.path.dirname(parent_dir)
        # add database folder to path
        backend_dir = os.path.join(backend_dir, "databases")
        path = os.path.abspath(backend_dir)
        if os.access(path, os.W_OK):
            print("Folder is writable.")
        else:
            print("Folder is not writable.")
        log("[CENTRAL]", f"Setting Up database backend directory: {path}")
        database_setup(path)
        await ctx.send("Bot setup complete.")
    
    @commands.command()
    async def setup_users(self, ctx):
        """
        Setup the users database.
        """
        log("[CENTRAL]", "INITIALIZING USERS DATABASE")
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:  # Skip bot accounts
                    print(f"Adding user {member.id} - {member}")
                    #if user doesnt esist in db, add them
                    await add_user(self.bot , member.id, member.name)
                    #add_user(member.id, str(member))


       

    def register_view(self, view_identifier, create_function):
        self.view_creators[view_identifier] = create_function

    async def add_view_to_database(self, view_identifier, view_registration, channel_id, category=""):
        conn = sqlite3.connect('backend/databases/views.db')
        c = conn.cursor()
        try:
            c.execute('''
                INSERT OR REPLACE INTO views 
                (view_id, view_registration, channel_id, timeout_date, disabled, reward, catagory)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (view_identifier, view_registration, channel_id, 0, 0, 0, category))
            conn.commit()
            log("[CENTRAL]", f"View {view_identifier} added to database.")
        except sqlite3.Error as e:
            log("[CENTRAL]", f"Error adding view to database: {e}")
        finally:
            conn.close()


    async def load_views(self):
        if not os.path.exists('backend/databases/views.db'):
            log("[CENTRAL]", "No views database found.")
            return False

        conn = sqlite3.connect('backend/databases/views.db')
        c = conn.cursor()
        c.execute('SELECT view_id, view_registration FROM views')
        rows = c.fetchall()
       
        for row in rows:
            view_identifier = row[0]
            view_registration = row[1]
            if view_registration in self.view_creators:
                view = self.view_creators[view_registration](view_identifier)
                self.bot.add_view(view)
            else:
                log("[CENTRAL]", f"No creator function found for view: {view_identifier} - {view_registration}")
                print(self.view_creators)
        conn.close()
        
        

async def setup(bot, config):
    log("[Central]", "Setting up Central cog...")
    await bot.add_cog(Central(bot, config))
   
