import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import sqlite3
import datetime

from common import log, get_time
from backend.users import *

DATABASE_PATH = "databases/drop_views.db"

class RewardView(View):
    def __init__(self, bot, view_id, channel_id, timeout_date, reward, cat):
        super().__init__(timeout=None)  # Timeout is managed by the background task
        self.bot = bot
        self.view_id = view_id
        self.channel_id = channel_id
        self.date = timeout_date
        self.is_timed_out = False
        self.add_item(RewardButton(bot, self, reward, cat))
        self.reward = reward
        self.cat = cat

    def update_view_state(self, disabled):
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("UPDATE views SET disabled = ? WHERE view_id = ?", (int(disabled), self.view_id))
        conn.commit()
        conn.close()

class RewardButton(Button):
    def __init__(self, bot, view, reward, cat):
        super().__init__(label='Claim Reward', style=discord.ButtonStyle.primary, custom_id=f'{view.view_id}')
        self.bot = bot
        self._view = view
        self.reward = reward # Use a different name to avoid conflict
        self.cat = cat

    @property
    def view(self):
        return self._view

    async def callback(self, interaction: discord.Interaction):
        current_time = int(time.time())
    
        if current_time >= self._view.date:
            await interaction.response.send_message('The timeout duration has already passed.', ephemeral=True)
            return
        if check_if_user_has_item(interaction.user.id, self.reward, f"{self.cat}s"):
            await interaction.response.send_message('You have already claimed this reward.', ephemeral=True)
            return
    
        else:
            # Reward the user
            print("REWARDING THE USER")
            if self.cat == "background":
                add_backgrounds_to_user(interaction.user.id, self.reward)
            elif self.cat == "title":
                add_title_to_user(interaction.user.id, self.reward) 
            elif self.cat == "color":
                add_color_to_user(interaction.user.id, self.reward)
            elif self.cat == "header":
                add_header_to_user(interaction.user.id, self.reward)
            else:
                print("somthing went wrong")
           
            await interaction.response.send_message('You have claimed your reward!', ephemeral=True)
            #await interaction.message.edit(view=self._view)


class RewardCog(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.load_views()

    def load_views(self):
        current_time = int(time.time())
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS views (
                        view_id INTEGER PRIMARY KEY,
                        channel_id INTEGER,
                        timeout_date INTEGER,
                        disabled INTEGER,
                        reward INTEGER,
                        catagory TEXT
                    )''')
        c.execute("SELECT view_id, channel_id, timeout_date, disabled, reward, catagory FROM views WHERE disabled = 0")
        rows = c.fetchall()
        for view_id, channel_id, timeout_date, disabled, reward, catagory in rows:
            if current_time < timeout_date:
                view = RewardView(self.bot, view_id, channel_id, timeout_date, reward, catagory)
                
                self.bot.add_view(view)
        conn.close()
    
    async def create_and_add_view_to_database(self, channel_id, timeout_date, reward_name, cat):
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO views (channel_id, timeout_date, disabled, reward, catagory) VALUES (?, ?, ?, ?, ?)',
                  (channel_id, timeout_date, 0, reward_name, cat))
        view_id = c.lastrowid 
        conn.commit()
        conn.close()
        view = RewardView(self.bot, view_id, channel_id, timeout_date, reward_name, cat)
        return view

    async def background_reward(self, reward_name, timeout_date):
        view = await self.create_and_add_view_to_database(self.config["REWARD_ID"], timeout_date, reward_name, "background")
        embed = discord.Embed(
            title=":loudspeaker: REWARD BACKGROUND AVAILABLE",
            description="Click the button below to claim A background reward.",
            color=discord.Color.blue()
        )
        channel = self.bot.get_channel(int(self.config["REWARD_ID"]))
        unix_timestamp = int(timeout_date)
        name, desc = get_name_of_item(reward_name, "background") 
        file = discord.File(f"images/p_backgrounds/{name}.png", filename=f"{name}.png")
        embed.set_image(url=f"attachment://{name}.png")
        embed.add_field(name="New Background", value=f"```{name}```", inline=False)
        embed.add_field(name="", value=f"*{desc}*", inline=False)
        embed.add_field(name="Dont lose out!", value=f"Reward Experation: <t:{unix_timestamp}:R>", inline=False)
        await channel.send(embed=embed, view=view, file=file)
        
    async def title_reward(self, reward_name, timeout_date):
        view = await self.create_and_add_view_to_database(self.config["REWARD_ID"], timeout_date,  reward_name, "title")
        embed = discord.Embed(
            title="Reward Available",
            description="Click the button below to claim A title reward.",
            color=discord.Color.blue()
        )
        channel = self.bot.get_channel(int(self.config["REWARD_ID"]))
        unix_timestamp = int(timeout_date)
        name, desc = get_name_of_item(reward_name, "title") 
        embed.add_field(name="New Title", value=f"```{name}```", inline=False)
        embed.add_field(name="", value=f"*{desc}*", inline=False)
        embed.add_field(name="Dont lose out!", value=f"Reward Experation: <t:{unix_timestamp}:R>", inline=False)
        await channel.send(embed=embed, view=view)

    async def color_reward(self, reward_name, timeout_date):
        view = await self.create_and_add_view_to_database(self.config["REWARD_ID"], timeout_date, reward_name, "color")
        embed = discord.Embed(
            title="Reward Available",
            description="Click the button below to claim A color reward.",
            color=discord.Color.blue()
        )
        channel = self.bot.get_channel(int(self.config["REWARD_ID"]))
        unix_timestamp = int(timeout_date)
        name, desc = get_name_of_item(reward_name, "color") 
        embed.add_field(name="New Color", value=f"```{name}```", inline=False)
        embed.add_field(name="", value=f"*{desc}*", inline=False)
        embed.add_field(name="Dont lose out!", value=f"Reward Experation: <t:{unix_timestamp}:R>", inline=False)
        await channel.send(embed=embed, view=view)

    async def header_reward(self, reward_name, timeout_date):
        view = await self.create_and_add_view_to_database(self.config["REWARD_ID"], timeout_date, reward_name, "header")
        embed = discord.Embed(
            title="Reward Available",
            description="Click the button below to claim A header reward.",
            color=discord.Color.blue()
        )
        channel = self.bot.get_channel(int(self.config["REWARD_ID"]))
        unix_timestamp = int(timeout_date)
        name, desc = get_name_of_item(reward_name, "header") 
        file = discord.File(f"images/p_headers/{name}.png", filename=f"{name}.png")
        embed.set_image(url=f"attachment://{name}.png")
        embed.add_field(name="New Header", value=f"```{name}```", inline=False)
        embed.add_field(name="", value=f"*{desc}*", inline=False)
        embed.add_field(name="Dont lose out!", value=f"Reward Experation: <t:{unix_timestamp}:R>", inline=False)
        await channel.send(embed=embed, view=view, file=file)
     
    
    
    @commands.command()
    async def create_reward_view(self, ctx, timeout_duration: int, reward_type: str, reward_name: str):
        current_time = int(time.time())
        timeout_duration = current_time + timeout_duration
        if reward_type == "background":
            await self.background_reward(reward_name, timeout_duration)
        elif reward_type == "title":
            await self.title_reward(reward_name, timeout_duration)
        elif reward_type == "color":
            await self.color_reward(reward_name, timeout_duration)

        elif reward_type == "header":
            await self.header_reward(reward_name, timeout_duration)
        else:
            pass


async def setup(bot, config):
    #name of your log(name of cog, print_info)
    log("SUPPLY_DROP", "Setting up Example cog...")
    await bot.add_cog(RewardCog(bot, config))
   