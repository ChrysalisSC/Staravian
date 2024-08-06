import discord
from discord.ext import commands, tasks
from discord import app_commands
import json


from common import log
import random
import asyncio
import sqlite3
import typing


def create_fishing_table():
    # Connect to SQLite database
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()

    # Create the fishing_table
    c.execute(
        """CREATE TABLE IF NOT EXISTS fishing_table (
                    user_id INTEGER,
                    thread_id INTEGER,
                    fishing_xp INTEGER DEFAULT 0,
                    total_fish_caught INTEGER DEFAULT 0,
                    total_fish_sold INTEGER DEFAULT 0,
                    fish_time INTERGER DEFAULT 1,
                    fishing_pool_stats TEXT DEFAULT '{}',
                    fish_inventory TEXT DEFAULT '{}'
                )"""
    )

    # Commit changes and close connection
    conn.commit()
    conn.close()


def get_fish_data(user_id):
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()
    c.execute("SELECT * FROM fishing_table WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data


def insert_thread_data(user_id, thread_id):
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()
    
    # Check if user already exists
    c.execute("SELECT * FROM fishing_table WHERE user_id=?", (user_id,))
    data = c.fetchone()
    
    if data:
        # Update thread ID for existing user
        c.execute("UPDATE fishing_table SET thread_id=? WHERE user_id=?", (thread_id, user_id))
    else:
        # Insert new user with thread ID
        c.execute(
            """INSERT INTO fishing_table (user_id, thread_id) 
            VALUES (?, ?)""",
            (user_id, thread_id),
        )
    conn.commit()

def remove_fish_from_inventory(user_id, fish_name, amount, fish_codes):
    # Connect to SQLite database
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()

    # Fetch existing user data including fish inventory and total fish sold
    c.execute("SELECT fish_inventory, total_fish_sold FROM fishing_table WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    

    

    if row:
        fish_inventory, total_fish_sold = json.loads(row[0]), row[1]

        # Check if the fish_input is a fish name or a fish code
        fish_name = fish_codes.get(fish_name, fish_name)
        fish_name = fish_name.lower()
        
        # Check if the fish exists in the inventory and if there are enough to remove
        print(f"fish_name: {fish_name}, invertory:{fish_inventory} amount: {amount}")
        if fish_name in fish_inventory and fish_inventory[fish_name] >= amount:
            fish_inventory[fish_name] -= amount
            
            # Remove the fish from the inventory if the count reaches zero
            if fish_inventory[fish_name] == 0:
                del fish_inventory[fish_name]
            
            # Convert the inventory back to JSON
            fish_inventory_json = json.dumps(fish_inventory)
            
            # Increment the total fish sold
            total_fish_sold += amount

            # Update the database with the new inventory and total fish sold
            c.execute(
                """UPDATE fishing_table
                   SET fish_inventory = ?, total_fish_sold = ?
                   WHERE user_id = ?""",
                (fish_inventory_json, total_fish_sold, user_id)
            )
            conn.commit()
            conn.close()
            return f"Removed {amount} {fish_name}(s) from user {user_id}'s inventory."
        else:
            conn.close()
            return f"Not enough {fish_name}(s) to remove. Operation failed."
    else:
        conn.close()
        return f"No inventory found for user {user_id}."

    

def update_fishing_table(user_id, thread_id, fish_name, xp_gained):
    # Connect to SQLite database
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()

    # Fetch existing user data
    c.execute("SELECT fishing_xp, total_fish_caught, fish_inventory FROM fishing_table WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
    row = c.fetchone()
    fish_name = fish_name.lower()

    if row:
        fishing_xp, total_fish_caught, fish_inventory = row
        
        # Update the user's fishing XP and total fish caught
        fishing_xp += xp_gained
        total_fish_caught += 1
        
        # Update the fish inventory
        fish_inventory = json.loads(fish_inventory)
        if fish_name in fish_inventory:
            fish_inventory[fish_name] += 1
        else:
            fish_inventory[fish_name] = 1
        fish_inventory = json.dumps(fish_inventory)
        
        # Update the database
        c.execute(
            """UPDATE fishing_table
               SET fishing_xp = ?, total_fish_caught = ?, fish_inventory = ?
               WHERE user_id = ? AND thread_id = ?""",
            (fishing_xp, total_fish_caught, fish_inventory, user_id, thread_id)
        )
    else:
        # If user not found, insert a new record
        fish_inventory = json.dumps({fish_name: 1})
        c.execute(
            """INSERT INTO fishing_table (user_id, thread_id, fishing_xp, total_fish_caught, fish_inventory)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, thread_id, xp_gained, 1, fish_inventory)
        )

    # Commit changes and close connection
    conn.commit()
    conn.close()



def update_fish_data(user_id, thread_id, new_stats, new_inventory):
    conn = sqlite3.connect("fish.db")
    c = conn.cursor()

    c.execute(
        """SELECT fishing_pool_stats, fish_inventory FROM fishing_table 
                 WHERE user_id = ? OR thread_id = ?""",
        (user_id, thread_id),
    )
    result = c.fetchone()

    if result:
        existing_stats = json.loads(result[0])
        existing_inventory = json.loads(result[1])
    else:
        existing_stats = {}
        existing_inventory = {}

    for pool, stats in new_stats.items():
        if pool in existing_stats:
            existing_stats[pool].update(stats)
        else:
            existing_stats[pool] = stats

    for fish, quantity in new_inventory.items():
        if fish in existing_inventory:
            existing_inventory[fish] += quantity
        else:
            existing_inventory[fish] = quantity

    updated_stats_json = json.dumps(existing_stats)
    updated_inventory_json = json.dumps(existing_inventory)

    c.execute(
        """UPDATE fishing_table SET fishing_pool_stats = ?, fish_inventory = ? 
                 WHERE user_id = ? OR thread_id = ?""",
        (updated_stats_json, updated_inventory_json, user_id, thread_id),
    )
    conn.commit()
    conn.close()


def pad_words(left_word, right_word, width):
    padding = ' ' * (width - len(left_word))
    return f"{left_word}{padding}{right_word}"


class Fish(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.fish_data = None
        self.load_fish_data()
        self.current_thread_ids = []
        self.fish_channel = 1239321686977941687
        create_fishing_table()  # Ensure table is created

    def load_fish_data(self):
        with open("games/fish/fish.json", "r") as file:
            self.fish_data = json.load(file)
            #print(self.fish_data)
        file.close()
        log("FISH", "Fish data loaded")


    @commands.command()
    async def fish_button(self, ctx):
        # Create View with button
        view_identifier = f"fish_view"
        view = discord.ui.View(timeout=86400)
        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Catch Nautilins!",
            custom_id=view_identifier,
        )
        view.add_item(button)

        # Get a random fishing pool
        fishing_pools = self.fish_data['pool_weights']
        items, probabilities = zip(*fishing_pools.items())
        fishing_pool_name = random.choices(items, probabilities, k=1)[0]

        # Choose one item randomly with weights
       
      
        fishing_pool = self.fish_data["fishing_pools"]
 
        fish = fishing_pool[fishing_pool_name]["fish"].keys()
        
        embed = discord.Embed(
            title=f"Nautilins - {fishing_pool_name}!",
            description=f"<@&1241651336718581850> A surplus of Nautilins has been spotted at the {fishing_pool_name}!",
            color=0xFFFFFF,
        )
        file = discord.File(f'images/nautilin/{fishing_pool[fishing_pool_name]['image']}')
        embed.set_image(url=f"attachment://{file.filename}")
    
        fish_string = ""
        for fish in fishing_pool[fishing_pool_name]["fish"]:
            rarity = self.fish_data['fishes'][fish]["type"]
            temp = pad_words(fish, rarity, 25)
       
            fish_string += f"{temp}\n"
            

        embed.add_field(name=f"", value=f"```{fish_string}```", inline=False)


        async def button_callback(interaction):
            try:
                ThreadManager = self.bot.get_cog("ThreadManager")
                if ThreadManager is not None:
                    thread = await ThreadManager.create_thread(
                        self.config["FISH_ID"], str(fishing_pool_name),1140 , 600, ctx.author
                    )
                  
                    if thread != False:
                        # await self.fishing_game(interaction.user.id)
                        await interaction.response.send_message(
                            f"The {fishing_pool_name} has opened up for you", ephemeral=True
                        )
                        insert_thread_data(interaction.user.id , thread.id)
                        await self.inital_fishing_message(thread.id, fishing_pool_name)
                        await self.fishing_game(thread.id, str(fishing_pool_name))
                    else:
                        await interaction.response.send_message(
                            "You already have a open thread", ephemeral=True
                        )
            except Exception as e:
                log("FISH", f"Error starting fishing game: {e}")
            return True

        # send embed with button
        button.callback = button_callback
        channel = self.bot.get_channel(int(self.config["FISH_ID"]))
        await channel.send(embed=embed, view=view, file=file)


    async def inital_fishing_message(self, thread_id, fishing_pool_name):
        fishing_pool = self.fish_data["fishing_pools"][fishing_pool_name]
        
        embed = discord.Embed(title=f"Welcome To The {fishing_pool_name}", color=0xFFFFFF)
        #send image of fishing pool and description
        file = discord.File(f'images/nautilin/{fishing_pool["image"]}')
        embed.set_image(url=f"attachment://{file.filename}")
        embed.add_field(name="Description", value=self.fish_data['fishing_pools'][fishing_pool_name]["description"], inline=False)
        channel = self.bot.get_channel(int(self.config["FISH_ID"]))
        thread = channel.get_thread(thread_id)

        await thread.send(embed=embed, file=file)
        return
        


    async def fishing_game(self, thread_id, fishing_pool_name):
        
        channel = self.bot.get_channel(int(self.config["FISH_ID"]))
        thread = channel.get_thread(thread_id)
        view_identifier = f"catch_fish"
        view = discord.ui.View(timeout=86400)
        fish_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Fish", )
        view.add_item(fish_button) 
        store_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Store", )
        view.add_item(store_button)
        embed = discord.Embed(title="Nautilins", description="Cast out your nautilin rod, visit the shop, or view your profile", color=0xFFFFFF)
        print(fishing_pool_name)
        fishing_pool = self.fish_data["fishing_pools"][fishing_pool_name]

        async def fish_button_callback(interaction): 

          

    
            fish = random.choices(list(fishing_pool["fish"].keys()), list(fishing_pool["fish"].values()), k=1)[0]
            print(f"fish: {fish}")
            embed = discord.Embed(title="You caught a nautilin!", description=f"You caught a {fish}", color=0xFFFFFF)
            file = discord.File(f'images/nautilin/{self.fish_data["fishes"][fish]['image']}')
            embed.set_image(url=f"attachment://{file.filename}")

            update_fishing_table(interaction.user.id, thread_id, fish, 10)
            await thread.send(embed=embed, file=file)

            await interaction.response.defer()
            await self.fishing_game(thread.id, fishing_pool_name)

            
          

        fish_button.callback = fish_button_callback
        
        await thread.send(embed=embed, view=view)
        return

    async def store_fish(self, ctx):
        pass

    @commands.command()
    async def fish_profile(self, ctx):
        user_id = ctx.author.id
        fish_data = get_fish_data(user_id)

        if fish_data:
            fishing_xp = fish_data[2]
            total_fish_caught = fish_data[3]
            total_fish_sold = fish_data[4]
            fishing_pool_stats = json.loads(fish_data[5])
            fish_inventory = json.loads(fish_data[6])

            embed = discord.Embed(title="Fish Profile", color=0xFFFFFF)
            embed.add_field(name="Fishing XP", value=fishing_xp)
            embed.add_field(name="Total Fish Caught", value=total_fish_caught)
            embed.add_field(name="Total Fish Sold", value=total_fish_sold)
            embed.add_field(name="Fishing Pools", value=", ".join(fishing_pool_stats.keys()))
            embed.add_field(name="Fish Inventory", value=", ".join(fish_inventory.keys()))
            

            if fishing_pool_stats:
                for pool, stats in fishing_pool_stats.items():
                    embed.add_field(name=f"{pool} Stats", value=f"Fish Caught: {stats['fish_caught']}, Fish Sold: {stats['fish_sold']}")

            if fish_inventory:
                inventory_str = ""
                for fish, quantity in fish_inventory.items():
                    inventory_str += f"{fish}: {quantity}\n"
                embed.add_field(name="Fish Inventory", value=inventory_str)

            await ctx.send(embed=embed)
        else:
            await ctx.send("No fish data found for this user.")



    @app_commands.command(
        name="nautilin",
        description="Information and commands for nautilins"
    )
    async def nautilin(self, interaction: discord.Integration, 
                       command:typing.Literal["Profile", "Shop", "Leaderboard"]):
        if command == "Profile":
            pass
        
    @app_commands.command(
        name="sell_nautilins",
        description="Sell a Nautilin for Silverleafs",
    )
    async def sell_nautilins(self, interaction: discord.Interaction, nautilin: str, amount: int):
        user_id = interaction.user.id
        print(f"found {nautilin} {amount}")
        message = remove_fish_from_inventory(user_id, nautilin, amount, self.fish_data["fish_codes"])
        await interaction.response.send_message(message)

        # add stuff here for adding the gold to the user
        
        
async def setup(bot, config):
    await bot.add_cog(Fish(bot, config))
