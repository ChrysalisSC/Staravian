import discord
from discord.ext import commands
from discord import app_commands

from backend.common.common import log, generate_random_number
import typing
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
import time
import pytz
from backend.utilities.users import *


DATABASE_PATH = 'backend/databases/shop_views.db'

class BuyButton(discord.ui.Button):
    def __init__(self, label, item_name, item_id, price, catagory):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.item_name = item_name
        self.price = price
        self.catagory = catagory
        self.item_id = item_id

    async def callback(self, interaction: discord.Interaction):
        #await interaction.response.defer()
        await interaction.response.send_message(f"Are you sure you want to buy '{self.item_name}' for {self.price}?", ephemeral=True, view=ConfirmationView(self.item_name, self.item_id, self.price, self.catagory))

class ConfirmationView(discord.ui.View):
    def __init__(self, item_name, item_id, price, catagory):
        super().__init__(timeout=None)
        self.item_name = item_name
        self.price = price
        self.catagory = catagory
        self.item_id = item_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (check_if_user_has_item(interaction.user.id, self.item_id, self.catagory)):
            await interaction.response.send_message(f"You already own the '{self.item_name}' background!", ephemeral=True)
            return
        if (check_and_update_credits(interaction.user.id, self.price)):
            await interaction.response.send_message(f" '{self.item_name}' purchased for {self.price}!", ephemeral=True)
            if self.catagory == "backgrounds":
                add_backgrounds_to_user(interaction.user.id, self.item_id)
            if self.catagory == "headers":
                add_header_to_user(interaction.user.id, self.item_id)
            if self.catagory == "titles":
                add_title_to_user(interaction.user.id, self.item_id)
            if self.catagory == "colors":
                add_color_to_user(interaction.user.id, self.item_id)
            return
        credits = get_user_credits(interaction.user.id)
        
        await interaction.response.send_message(f"You do not have enough Arcanum. You have {credits} Arcanum and need {self.price - credits} more", ephemeral=True)

    #@discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    #async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        #await interaction.response.send_message("Purchase cancelled.", ephemeral=True)


async def shop_backgrounds(thread, shop_name, data, catagory):
    
    backgrounds = data['collections'][shop_name]['backgrounds']
    images = []
    embed = discord.Embed(title="PROFILE BACKGROUNDS", description="Choose a background to purchase, Our wares are ordered from left to right, top to bottom: ", color=discord.Color.blue())
    for key, value in backgrounds.items():
        name = value['name']
        price = value['price']
        image_path = f"images/p_backgrounds/{value['image']}"
        
        # Open the image file and create a discord.File object
        file =  discord.File(image_path, filename=image_path)
        images.append(file)
        
        # Add fields to the embed
    
        embed.add_field(name=name, value=value['description'],inline=True)
        embed.add_field(name="Price",value=f"{price} <:credit:1252401089781694604>'s", inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.set_image(url=f"attachment://images/p_backgrounds/{value['image']}")
    await thread.send(embed=embed, files=images, view=ShopView(backgrounds, catagory))

async def shop_headers(thread, shop_name, data, catagory):
    print("DATA", data)

    backgrounds = data['collections'][shop_name]['headers']
    images = []
    embed = discord.Embed(title="PROFILE HEADERS", description="Choose a header to purchase:", color=discord.Color.blue())
    for key, value in backgrounds.items():
        name = value['name']
        price = value['price']
        image_path = f"images/p_headers/{value['image']}"
        
        # Open the image file and create a discord.File object
        file =  discord.File(image_path, filename=image_path)
        images.append(file)
        
        # Add fields to the embed
    
        embed.add_field(name=name, value=value['description'],inline=True)
        embed.add_field(name="Price",value=f"{price} <:credit:1252401089781694604>'s", inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.set_image(url=f"attachment://images/p_headers/{value['image']}")
    await thread.send(embed=embed, files=images, view=ShopView(backgrounds, catagory))

async def shop_titles(thread, shop_name, data, catagory):
    
    backgrounds = data['collections'][shop_name]['titles']
    embed = discord.Embed(title="PROFILE TITLES", description="Choose a title to purchase:", color=discord.Color.blue())
    for key, value in backgrounds.items():
        name = value['name']
        price = value['price']

        embed.add_field(name=name, value=value['description'],inline=True)
        embed.add_field(name="Price",value=f"{price} <:credit:1252401089781694604>'s", inline=True)
        embed.add_field(name="", value="", inline=False)
       
    await thread.send(embed=embed, view=ShopView(backgrounds, catagory))

async def shop_colors(thread, shop_name, data, catagory):
    backgrounds = data['collections'][shop_name]['colors']
 
    embed = discord.Embed(title="PROFILE COLORS", description="Choose a color to purchase:", color=discord.Color.blue())
    for key, value in backgrounds.items():
        name = value['name']
        price = value['price']

        embed.add_field(name=name, value=value['description'],inline=True)
        embed.add_field(name="Price",value=f"{price} <:credit:1252401089781694604>'s", inline=True)
        embed.add_field(name="", value="", inline=False)
       
    await thread.send(embed=embed, view=ShopView(backgrounds, catagory))



class ShopView(discord.ui.View):
    def __init__(self, items, catagory):
        super().__init__(timeout=None)
        for item in items.values():
            print(item)
            name = item['name']
            item_id = item['id']
            price = item['price']
            #print(background_id)
            self.add_item(BuyButton(label=f"Buy {name}", item_name=name,item_id=item_id, price=price, catagory=catagory))

class ShopWelcomeView(discord.ui.View):
    def __init__(self, thread, shop_name, data, timeout=None):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Backgrounds", style=discord.ButtonStyle.primary, custom_id="backgrounds"))
        self.add_item(discord.ui.Button(label="Headers", style=discord.ButtonStyle.primary, custom_id="headers"))
        self.add_item(discord.ui.Button(label="Titles", style=discord.ButtonStyle.primary, custom_id="titles"))
        self.add_item(discord.ui.Button(label="Colors", style=discord.ButtonStyle.primary, custom_id="colors"))
        self.thread = thread
        self.shop_name = shop_name
        self.data = data

    async def interaction_check(self, interaction: discord.Interaction):
        # Check which button was pressed and create the appropriate ShopView
        #await interaction.response.defer()
        await interaction.response.send_message(f"Loading {interaction.data["custom_id"]} Please wait...", ephemeral=True)
        if interaction.data["custom_id"] == "backgrounds":
           await shop_backgrounds(self.thread, self.shop_name, self.data, interaction.data["custom_id"])

        elif interaction.data["custom_id"] == "headers":
            await shop_headers(self.thread, self.shop_name, self.data, interaction.data["custom_id"])

        elif interaction.data["custom_id"] == "titles":
            await shop_titles(self.thread, self.shop_name, self.data, interaction.data["custom_id"])

        elif interaction.data["custom_id"] == "colors":
            await shop_colors(self.thread, self.shop_name, self.data, interaction.data["custom_id"])

        return True

def get_shop_name():
    # Load the JSON data from the file
    json_file = "config/shared_config/post.json"
    with open(json_file, 'r') as file:
        data = json.load(file)
    file.close()
    # Get the current trading post name
    current_post_name = data["current_trading_post"]["name"]
    description = data["trading_post_rotation"][current_post_name]["description"]
    
    return current_post_name, description

def update_trading_post():
    json_file = "config/shared_config/post.json"
    # Load the JSON data from the file
    with open(json_file, 'r') as file:
        data = json.load(file)
    file.close()
    # Get the current trading post name
    current_post_name = data["current_trading_post"]["name"]
    
    # Find the next trading post
    next_post_name = data["trading_post_rotation"][current_post_name]["next"]
    
    # Update the current trading post to the next one
    data["current_trading_post"]["name"] = next_post_name
    data["current_trading_post"]["next"] = data["trading_post_rotation"][next_post_name]["next"]
    
    # Save the updated data back to the file
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)
    file.close()

class Shop(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.load_views()
    

    def get_username(self, user_id):
        member = self.bot.get_user(user_id)
        if member:
            return member.display_name
        else:
            return "Unknown"
        
    def load_views(self):
        #current_time = int(time.time())
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS shop_views (
                    view_id SRING,
                    channel_id INTEGER,
                    end_time INTEGER,
                    shop_name STRING
                )''')
        c.execute("SELECT view_id, channel_id, end_time, shop_name FROM shop_views WHERE end_time > ?", (int(time.time()),))
        rows = c.fetchall()
        for view_id, channel_id, end_time, shop_name in rows:
            channel = self.bot.get_channel(channel_id)
            if channel:
                view = self.create_shop_view(view_id, end_time, shop_name)
                self.bot.add_view(view)
        conn.close()

    def create_shop_view(self, view_id, end_time, shop_name):
        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Visit The Trading Post",
            custom_id=f"{view_id}"
        )
        view.add_item(button)

        async def button_callback(interaction):
            try:
                ThreadManager = self.bot.get_cog("ThreadManager")
                if ThreadManager is not None:
                    thread = await ThreadManager.create_thread(
                        self.config["SHOP_ID"], "Shop Stall", 1140, 600, interaction.user
                    )

                    if thread != False:
                        await interaction.response.send_message(
                            f"The Trading Post entreats you to explore its collections!", ephemeral=True
                        )
                        await self.shop_start(thread, shop_name, interaction.user.id,)
                    else:
                        await interaction.response.send_message(
                            "You already have an open thread", ephemeral=True
                        )
            except Exception as e:
                log("SHOP", f"Error starting shop: {e}")
            return True

        button.callback = button_callback
        return view
        
  
    async def shop_start(self, thread, shop_name, user_id):
        #create_shopembed
       
   
        with open("config/shared_config/backgrounds.json") as f:
            data = json.load(f)
        f.close()

        await self.welcome_shop(thread, shop_name, data, user_name=self.get_username(user_id), user_id=user_id)


     
    

    async def welcome_shop(self, thread, shop_name, data, user_name, user_id):
        view = ShopWelcomeView(thread, shop_name, data)
        description = data['collections'][shop_name]['description']

        embed = discord.Embed(title=f"Welcome to the Shop {user_name}! You have {get_user_credits(user_id)} Arcanum to spend", description="Choose a category to shop for upgrades:", color=discord.Color.blue())
        embed.add_field(name=f"The Current trading post is offering selections from the {shop_name} collection.", value="Backgrounds, Headers, Titles, Colors", inline=False)
        embed.add_field(name="Description", value=description, inline=False)
        
        await thread.send(embed=embed, view=view)
        

    """
    @commands.command()
    async def shop(self, ctx):
        # Create View with button
        view_identifier = f"shop_view"
        view = discord.ui.View(timeout=86400)
        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Visit The Trading Post ",
            custom_id=view_identifier,
        )
        view.add_item(button)
        embed = discord.Embed(title=":loudspeaker: Trading Post", description="The Trading Post is open for business! Come and see what new items are available for purchase.", color=0xFFFFFF)

        shop_name, desc = get_shop_name()
        
        random_image = generate_random_number(10)
        file = discord.File(f"images/trading_post/{random_image}.jpg", filename="image.jpg")
        embed.add_field(name=f"THIS WEEK'S OFFERINGS - The **{shop_name}** collection!", value=f"{desc}", inline=False)
        embed.set_image(url="attachment://image.jpg")
       
        end_time = datetime.datetime.now(pytz.utc) + timedelta(hours=168)
        unix_timestamp = int(end_time.timestamp())
        embed.add_field(name="", value=f":x: **DONT MISS OUT! CLOSES:** <t:{unix_timestamp}:R>", inline=False)
        async def button_callback(interaction):
            try:
                ThreadManager = self.bot.get_cog("ThreadManager")
                if ThreadManager is not None:
                    thread = await ThreadManager.create_thread(
                        self.config["SHOP_ID"], "Shop Stall" ,1140 , 600, ctx.author
                    )
                  
                    if thread != False:
                        # await self.fishing_game(interaction.user.id)
                        await interaction.response.send_message(
                            f"The Trading Post entreats you to explore its collections!", ephemeral=True
                        )
                      
                        #await self.inital_fishing_message(thread.id, fishing_pool_name)
                        #await self.fishing_game(thread.id, str(fishing_pool_name))
                        await self.shop_start(thread, str(shop_name), interaction.user.id)
                        
                    else:
                        await interaction.response.send_message(
                            "You already have a open thread", ephemeral=True
                        )
            except Exception as e:
                log("SHOP", f"Error starting shop: {e}")
            return True
   
        button.callback = button_callback
        channel = self.bot.get_channel(1249928122309021776)
        await channel.send(embed=embed, view=view, file=file)
        """
    async def shop(self):
        #get channel from config

        channel_name = self.bot.get_channel(int(self.config["SHOP_ID"]))

        view_identifier = f"shop_view"
        end_time = datetime.datetime.now(pytz.utc) + timedelta(hours=168)
        unix_timestamp = int(end_time.timestamp())
        embed = discord.Embed(
            title=":loudspeaker: Trading Post",
            description="The Trading Post is open for business! Come and see what new items are available for purchase.",
            color=0xFFFFFF
        )
        
        shop_name, desc = get_shop_name()
        random_image = generate_random_number(10)
        file = discord.File(f"images/trading_post/{random_image}.jpg", filename="image.jpg")
        embed.add_field(name=f"THIS WEEK'S OFFERINGS - The **{shop_name}** collection!", value=f"{desc}", inline=False)
        embed.set_image(url="attachment://image.jpg")
        embed.add_field(name="", value=f":x: **DONT MISS OUT! CLOSES:** <t:{unix_timestamp}:R>", inline=False)

        view = self.create_shop_view(view_identifier + "_" + shop_name, unix_timestamp, shop_name)

        message = await channel_name.send(embed=embed, view=view, file=file)
        
        # Store view in the database
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO shop_views (view_id, channel_id, end_time, shop_name) VALUES (?, ?, ?, ?)",
                  (view_identifier + "_" + shop_name , channel_name.id, unix_timestamp, shop_name))
        conn.commit()
        conn.close()

       
       
      
     
        
        
       


async def setup(bot, config):
    #name of your log(name of cog, print_info)
    log("SHOP", "SHOP SETTING UP...")
    await bot.add_cog(Shop(bot, config))
   

