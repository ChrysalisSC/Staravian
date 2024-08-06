import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

import datetime


from common import log
import json

from backend.users import *
from backend.renown import create_table_renown

from PIL import Image, ImageDraw, ImageFont
import os


"""
This file contains the Users cog, which is responsible for managing user data such as XP, credits, and levels.
It has the following funtions and classes:

- get_user_xp(user_id)
- get_user_credits(user_id)
- get_user_data(user_id)
- update_user_xp(user_id, xp)
- update_user_credits(user_id, credits)
- check_level_up(xp,total_xp,level)
- get_level(current_level, total_xp, experience_table)
- add_buff_to_user(user_id, buff)
- remove_buff_from_user(user_id, buff)
- Users(commands.Cog)
- create_table(self)
- get_username(self, user_id)
- get_member_by_id(self, user_id)
- async def setup(bot, config)

The Users table has the following idexes (name - index):
- (0) user_id - PRIMARY KEY 
- (1) username
- (2) credits
- (3) total_xp
- (5) level
- (6) role_name
- (7) team_name
- (8) buffs
- (9) titles
- (10) guild
- (11) daily_lockout
- (12) weekly_lockout
- (13) header_background
- (14) profile_background
"""

import requests
import ast

def add_emote_grid(image, emotes, grid_size=(5, 3), emote_size=(30, 30), padding=5):
    draw = ImageDraw.Draw(image)
    grid_width, grid_height = grid_size
    emote_width, emote_height = emote_size

    # Calculate starting positions
    start_x = (image.width - (emote_width * grid_width + padding * (grid_width - 1))) // 2
    start_y = 3  # Starting Y position for the grid below the text

    for row in range(grid_height):
        for col in range(grid_width):
            emote_index = row * grid_width + col
            if emote_index < len(emotes):
                emote = emotes[emote_index].resize(emote_size)
                x = start_x + col * (emote_width + padding)
                y = start_y + row * (emote_height + padding)
                image.paste(emote, (x, y), emote)

    return image

class Users(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.db_conn = sqlite3.connect('user_data.db')
        self.cursor = self.db_conn.cursor()
        self.config = config


    def get_username(self, user_id):
        member = self.bot.get_user(user_id)
        if member:
            return member.name
        else:
            return "Unknown"
        
    async def get_member_by_id(self, user_id):
        guild = self.bot.get_guild(1226714258117496922)
        if guild:
            member = guild.get_member(user_id)
            if member:
                return member
        return None

    

    
    
    
    async def create_profile_card(self, username, member, level, xp, needed_xp, background, header, color, credits, title, timespent, last_seen,badges, profile_picture_path, output_path):

        #FONTS
        font = ImageFont.truetype("arial.ttf", 18)
        bottom_font =  ImageFont.truetype("arial.ttf", 18)
        COIN_FONT  =  ImageFont.truetype("arial.ttf", 50)
        RANK_FONT = ImageFont.truetype("arial.ttf", 25)
        HEADER_FONT = ImageFont.truetype("arialbd.ttf", 30)
        TITLE_FONT = ImageFont.truetype("arialbd.ttf", 20)
        LEVEL_FONT = ImageFont.truetype("arial.ttf", 15)
        #FIX COLOR
        color = ast.literal_eval(color)

         # Load profile picture
        profile_picture = Image.open(profile_picture_path).resize((100, 100)).convert("RGBA")
        
        base_image = Image.open(f"images/p_headers/{header}.png")  # Replace "path_to_your_base_image.jpg" with the path to your base image
        card = base_image.resize((400, 120))
        width, height = 400, 120
    
        profile_position = (width - 110, 10)  # Adjust the position as needed
        border_color = (0, 0, 0, 255)  # Black border color
        border_thickness = 2  # Border thickness in pixels
        draw = ImageDraw.Draw(card)
        draw.rectangle([(profile_position[0] - border_thickness, profile_position[1] - border_thickness),
                        (profile_position[0] + 100 + border_thickness-1, profile_position[1] + 100 + border_thickness -1)],
                    outline=border_color, width=border_thickness)
        card.paste(profile_picture, profile_position, mask=profile_picture)
        
        # Draw username
      
        draw.text((5, 5), f"{username}", fill="white", font=HEADER_FONT, stroke_width=2, stroke_fill=(20,20,20))
        draw.text((8, 40), f"{title}", fill="white", font=TITLE_FONT,stroke_width=2, stroke_fill=(20,20,20))

        #Calculate level text widths
        level_text = f"{level}"
        level_text_width = len(level_text) * 6
        level_text = "Level " + level_text 
        level_size = 45
        progress_width = int(((xp / needed_xp) * 100) / 100 * 270)
        
        # Draw level bar and texts
        draw.text((12, 83), f"{xp} / {needed_xp} XP", fill="white", font=LEVEL_FONT, stroke_width=2, stroke_fill=(20,20,20))
        draw.text((280 - (level_size + level_text_width), 83), level_text, fill="white", font=LEVEL_FONT, stroke_width=2, stroke_fill=((20,20,20)))
        draw.rectangle([(10, 100), (280, 110)], fill=(20,20,20), outline=(20,20,20))
        draw.rectangle([(10, 100), (10 + progress_width, 110)], fill=color, outline=(20,20,20))
 
        profile_card = Image.new("RGBA", (400, 320), (255, 255, 255, 255))
        profile_background = Image.open(f"images/P_backgrounds/{background}.png").resize((400, 200)).convert("RGBA")
      
        profile_card.paste(profile_background, (0, 120))

        # Paste the initial card at the top of the new image
        border_color = (150, 150, 150, 255)
        profile_card.paste(card, (0, 0))
        draw_profile_card = ImageDraw.Draw(profile_card)

        draw_profile_card.rectangle([(0, 120), (400 , 123)], outline=border_color, width=3)
  
        join_date = Image.new("RGBA", (120,40), (128, 128, 128, 150))
        draw = ImageDraw.Draw(join_date)
        text = "JOIN DATE"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (120 - text_width_join) // 2
        y = (40 - text_height_join) // 2
        draw.text((x, 0), text, fill="white", font=font)
        
        text =  str(member.joined_at.strftime('%d %b %y'))
        print("TEXT", text)
        bbox = draw.textbbox((0, 0), str(text), font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (120 - text_width_join) // 2
        y = (40 - text_height_join) // 2


        draw.text((x, 17), text, fill=color, font=bottom_font)
        profile_card.paste(join_date, (10, 130), join_date)

        #LAST SEEN BOX
        last_seen_box = Image.new("RGBA", (120,40), (128, 128, 128, 150))
        draw = ImageDraw.Draw(last_seen_box)
        text = "LAST SEEN"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (120 - text_width_join) // 2
        y = (40 - text_height_join) // 2
  
        draw.text((x, 0), text, fill="white", font=font)
        # formate last seen
       
        last_seen_date = datetime.datetime.fromisoformat(last_seen).strftime('%d %b %y')
        print("LAST SEEN", last_seen_date)
        bbox = draw.textbbox((0, 0),str(last_seen_date), font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (120 - text_width_join) // 2
        y = (40 - text_height_join) // 2
  
        draw.text((x, 17), last_seen_date, fill=color, font=bottom_font)
        profile_card.paste(last_seen_box, (140, 130), last_seen_box)

        box_3 = Image.new("RGBA", (120,40), (128, 128, 128, 150))
        draw = ImageDraw.Draw(box_3)
        text = "ACTIVITY"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (120 - text_width_join) // 2
        y = (40 - text_height_join) // 2
        draw.text((15, 0), text, fill="white", font=font)

        text = str(timespent) #FIX ME FOR CORRECT TIME
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (120 - text_width_join) // 2
        y = (40 - text_height_join) // 2
  
        draw.text((x, 17), text, fill=color, font=bottom_font)
        profile_card.paste(box_3, (270, 130), box_3)

        #overlay = Image.new("RGBA", (overlay_width, overlay_height), (128, 128, 128, 150))
        #profile_card.paste(overlay, (10, 130), overlay) #10,130 is the position of the overlay
        box_4 = Image.new("RGBA", (190,40), (128, 128, 128, 150))
        draw = ImageDraw.Draw(box_4)
        text = "RANK #1"
        bbox = draw.textbbox((0, 0), text, font=RANK_FONT)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center

        x = (190 - text_width_join) // 2
        y = (40 - text_height_join) // 2
        draw.text((x, y-5), text, fill="white", font=RANK_FONT)
        profile_card.paste( box_4, (10, 180),  box_4)
        """
        box_5 = Image.new("RGBA", (180,130), (128, 128, 128, 150))
        draw = ImageDraw.Draw(box_5)
        text = "BADGES"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (180 - text_width_join) // 2
        y = (130 - text_height_join) // 2
        draw.text((x, (120 - text_height_join)), text, fill="white", font=font)
        profile_card.paste( box_5, (210, 180),  box_5)
        """
        box_5 = Image.new("RGBA", (180, 130), (128, 128, 128, 150))
        draw = ImageDraw.Draw(box_5)
        text = "BADGES"
        font = ImageFont.truetype("arial.ttf", 20)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (180 - text_width_join) // 2
        y = (130 - text_height_join) // 2
        draw.text((x, (120 - text_height_join)), text, fill="white", font=font)
        #Load example emotes (replace with your actual emote images)
        with open("shared_config/badges.json", "r") as file:
            badge_data = json.load(file)
        file.close()

        emotes = [Image.open(f"images/badges/{badge_data[badge['badge']]["image"]}") for badge in badges]
        print("EMOTES", emotes)
        # Add the emote grid to the box
        box_5 = add_emote_grid(box_5, emotes)
        profile_card.paste(box_5, (210, 180), box_5)
     


        box_6 = Image.new("RGBA", (190,80), (128, 128, 128, 150))
        draw = ImageDraw.Draw(box_6)
        text = str(credits)
        bbox = draw.textbbox((0, 0), text, font=COIN_FONT)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (190 - text_width_join) // 2
        y = (80 - text_height_join) // 2
        draw.text((x, 0), text, fill="white", font=COIN_FONT)

        text = "ARCANUM"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width_join = bbox[2] - bbox[0]
        text_height_join = bbox[3] - bbox[1]
        # Position the text in the center
        x = (190 - text_width_join) // 2
        y = (80 - text_height_join) // 2


        draw.text((x, (70 - text_height_join)), text, fill=color, font=bottom_font)
        profile_card.paste(box_6, (10, 230), box_6)
        

        profile_card.save(output_path)
    
    async def tavern_profile(self, thread, member):
        # Get the username and profile picture of the Discord user


        username = (str(member.display_name)).upper()
        
        if member.avatar:
            thumbnail_url = str(member.avatar.url)
        else:
            # Set to default profile picture URL
            thumbnail_url = str(member.default_avatar.url)
       
            #await thread.send("Failed to retrieve member information.")
            

        # Output path for the profile picture
        profile_picture_path = "temp_profile_picture.png"
        
        # Download the profile picture from the URL and save it to a temporary file
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            with open(profile_picture_path, "wb") as f:
                f.write(response.content)


            #user_data = get_user_data(member.id)
            # Output path for the profile card image
            #set the databelow using the user_data
            
            xp = get_user_xp(member.id)
            print("XP", xp)
            level = get_level(xp)
            xp = xp - get_xp_needed(level - 1)
            needed_xp = get_xp_needed(level) - get_xp_needed(level - 1)

    
            background, header, title, color = get_user_profile_names(member.id)

            output_path = "profile_card.png"

            print(xp, needed_xp, title, level)
           
            credits = get_user_credits(member.id)
            timespent = get_time_spent(member.id)
            last_seen = get_last_seen(member.id)
            badges = get_all_user_badges(member.id)
            #last_seen = "FIX ME"
            print(f"username: {username}, level: {level}, xp: {xp}, needed_xp: {needed_xp}, background: {background}, header: {header}, color: {color}, credits: {credits}, title: {title}, timespent: {timespent}, last_seen: {last_seen}, badges: {badges}, profile_picture_path: {profile_picture_path}, output_path: {output_path}")
            await self.create_profile_card(username, member, level, xp, needed_xp, background, header, color, credits, title, timespent, last_seen, badges, profile_picture_path, output_path)
            file = discord.File(output_path)
            await thread.send( file=file)
            os.remove(profile_picture_path)
        else:
            await thread.send("Failed to download the profile picture.")
        

  
    @commands.command()
    async def profile(self, ctx):
        # Get the username and profile picture of the Discord user
        member = ctx.author
        username = (str(member.display_name)).upper()
        
        if member:
            thumbnail_url = str(member.avatar.url)
        else:
            await ctx.send("Failed to retrieve member information.")
            return

        # Output path for the profile picture
        profile_picture_path = "temp_profile_picture.png"
        
        # Download the profile picture from the URL and save it to a temporary file
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            with open(profile_picture_path, "wb") as f:
                f.write(response.content)

            # Output path for the profile card image
            output_path = "profile_card.png"
            level = 22
            xp = 9
            total_xp = 10
            title = "Stardust Novice"

            # Call the create_profile_card function with the provided parameters
            await self.create_profile_card(username, level, xp, total_xp, profile_picture_path,  output_path, title)

            # Send the profile card image to the Discord channel

            # embed = discord.Embed(title="PROFILE", description="") 
            file = discord.File(output_path)

            #embed = discord.Embed(title="PROFILE", description="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            #embed.set_image(url="attachment://profile_card.png")

            await ctx.send( file=file)
            

            os.remove(profile_picture_path)
        else:
            await ctx.send("Failed to download the profile picture.")
        

    
    @commands.command()
    async def addUser(self, ctx, *, member: discord.Member):
        username = self.get_username(member.id)
        await add_user(self.bot , member.id, member.name)
        await ctx.send(f"User {username} added to the database")

    @commands.command()
    async def addcredits(self, ctx, *, member: discord.Member):
        username = self.get_username(member.id)
        add_user_credits(member.id, 1000)
        await ctx.send(f"User {username} added to the database")

   
    def create_view_table(self):
       
        conn = sqlite3.connect('databases/views.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS views (
                view_identifier TEXT PRIMARY KEY
            )
        ''')
        conn.commit()
        conn.close()



    @commands.command()
    async def start(self, ctx, *, member: discord.Member):
        username = self.get_username(member.id)
        create_table()
        create_table_renown()
        self.create_view_table()
        add_user(member.id, member.name)
        add_user_credits(member.id, 1000)
        add_backgrounds_to_user(member.id,"green")
        
        add_header_to_user(member.id, "green")
        add_header_to_user(member.id,"red")
        add_badge_to_user(member.id, "credit")
        add_color_to_user(member.id,"green")
        add_color_to_user(member.id,"red")
        add_user_credits(member.id, 1000)
        add_title_to_user(member.id, "novice")
        set_title(member.id, "novice")
        await ctx.send("Finished_setup")

    @commands.command()
    async def addtitlest(self, ctx, *, member: discord.Member):
        for i in range(2,26):
            add_title_to_user(member.id, f"Title {i}")
      
        add_backgrounds_to_user(member.id,"green")
        add_header_to_user(member.id, "green")
        add_header_to_user(member.id,"red")
        add_badge_to_user(member.id, "credit")
        add_color_to_user(member.id,"green")
        add_color_to_user(member.id,"red")
        add_user_credits(member.id, 1000)

    @commands.command()
    async def add_color(self, ctx, member: discord.Member, color: str):
        add_color_to_user(member.id, color)
        await ctx.send("Color added")

    @commands.command()
    async def add_background(self, ctx, member: discord.Member, color: str):
        add_backgrounds_to_user(member.id, color)
        await ctx.send("background added")

    
    @commands.command()
    async def add_renown_table(self, ctx):
        create_table_renown()
        await ctx.send("Renown table created")

    @commands.command()
    async def add_badge(self, ctx, member: discord.Member, badge: str):
        add_badge_to_user(member.id, badge)
        await ctx.send("Badge added")

    @commands.command()
    async def madmin(self, ctx, member: discord.Member):
        set_admin(member.id)
        await ctx.send("Role added")

    @commands.command()
    async def set_xp(self, ctx, member: discord.Member, xp: int):
        set_xp(member.id, xp)
        await ctx.send("XP set")

    @commands.command()
    async def resetme(self, ctx, member: discord.Member):


        user = get_user_data(member.id)
        user_id = user[0]
        username = user[1]
        last_seen = get_time()
        conn = sqlite3.connect("databases/user_data.db")
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO USERINFO (
                user_id, username, credits, total_xp, level, role_name,
                team_name, buffs, titles, selected_title, guild,
                daily_lockout, weekly_lockout, header_backgrounds, set_header_background,
                profile_backgrounds, selected_background, profile_colors,
                selected_color, badges, selected_badges, timespent, last_seen, is_admin
            ) VALUES (?, ?, 0, 0, 1, NULL, NULL, '[]', '["novice"]','novice', NULL, 0, 0, '["blue"]', 'blue', '["blue"]', 'blue', '["blue"]', 'blue', '[]', '[]', 0, ?, 0)
        ''', (user_id, username, last_seen))
        conn.commit()
        conn.close()

    @commands.command()
    async def setup_bot(self, ctx):
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:  # Skip bot accounts
                    print(f"Adding user {member.id} - {member}")
                    #if user doesnt esist in db, add them
                    await add_user(self.bot, member.id, str(member))
                
            
async def setup(bot, config):
    log("USERS", "Setting up Users cog...")
    await bot.add_cog(Users(bot, config))