import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import time
import base64
import os
import json

from common import log, generate_random_number, get_time
from datetime import datetime, timezone, timedelta
import pytz
from PIL import Image, ImageDraw, ImageFont

from backend.users import *
import ast

import requests


class levelup(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    async def create_profile_card(self, username, level, xp, total_xp, profile_picture_path, output_path, title):
        # Load profile picture
        
        profile_picture = Image.open(profile_picture_path).resize((100, 100)).convert("RGBA")

        base_image = Image.open("images/IMG_2552.png")  # Replace "path_to_your_base_image.jpg" with the path to your base image
        card = base_image.resize((400, 120))

        # Create a blank image with white background
        width, height = 400, 120
        #card = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))

        # Draw the profile picture with a border
        profile_position = (width - 110, 10)  # Adjust the position as needed
        border_color = (0, 0, 0, 255)  # Black border color
        border_thickness = 2  # Border thickness in pixels
        draw = ImageDraw.Draw(card)
        draw.rectangle([(profile_position[0] - border_thickness, profile_position[1] - border_thickness),
                        (profile_position[0] + 100 + border_thickness-1, profile_position[1] + 100 + border_thickness -1)],
                    outline=border_color, width=border_thickness)
        card.paste(profile_picture, profile_position, mask=profile_picture)
        border_color = (150, 150, 150, 255)  # Black border color
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=border_color, width=border_thickness)
        
        # Draw username
        font = ImageFont.truetype("arialbd.ttf", 30)
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        level_font = ImageFont.truetype("arial.ttf", 15)
        draw.text((5, 5), f"{username}", fill="white", font=font, stroke_width=2, stroke_fill=(20,20,20))
        draw.text((8, 40), f"The {title}", fill="white", font=font_title,stroke_width=2, stroke_fill=(20,20,20))

        #Calculate level text widths
        level_text = f"{level}"
        level_text_width = len(level_text) * 6
        level_text = "Level " + level_text 
        level_size = 45
        progress_width = int(((xp / total_xp) * 100) / 100 * 270)
        
        # Draw level bar and texts
        draw.text((12, 83), f"{xp} / {total_xp} XP", fill="white", font=level_font, stroke_width=2, stroke_fill=(20,20,20))
        draw.text((280 - (level_size + level_text_width), 83), level_text, fill="white", font=level_font, stroke_width=2, stroke_fill=((20,20,20)))
        draw.rectangle([(10, 100), (280, 110)], fill=(20,20,20), outline=(20,20,20))
        draw.rectangle([(10, 100), (10 + progress_width, 110)], fill=(0, 191, 255), outline=(20,20,20))
 
        profile_card = Image.new("RGBA", (400, 320), (200, 200, 200, 255))
        
        # Paste the initial card at the top of the new image
        profile_card.paste(card, (0, 0))
        # Save the new extended profile card
        profile_card.save(output_path)

    async def create_profile_card_2(self, username, level, xp, total_xp, profile_picture_path, output_path, title):
        profile_card = Image.new("RGBA", (400, 320), (10, 10, 10, 255))
        
        # Paste the initial card at the top of the new image
     
        # Save the new extended profile card
        profile_card.save(output_path)
    

    async def get_member_by_id(self, user_id):
        guild = self.bot.get_guild(self.config['GUILD_ID'])  
        if guild:
            member = guild.get_member(user_id)
            if member:
                return member
        return None
    
    async def create_level_card(self, username, level, xp, needed_xp, header, profile_picture_path, output_path, title, color):
        # Load profile picture
        """
        profile_picture = Image.open(profile_picture_path).resize((100, 100)).convert("RGBA")

        base_image = Image.open("images/IMG_2552.png")  # Replace "path_to_your_base_image.jpg" with the path to your base image
        card = base_image.resize((400, 120))

        # Create a blank image with white background
        width, height = 400, 120
        #card = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))

        # Draw the profile picture with a border
        profile_position = (width - 110, 10)  # Adjust the position as needed
        border_color = (0, 0, 0, 255)  # Black border color
        border_thickness = 2  # Border thickness in pixels
        draw = ImageDraw.Draw(card)
        draw.rectangle([(profile_position[0] - border_thickness, profile_position[1] - border_thickness),
                        (profile_position[0] + 100 + border_thickness-1, profile_position[1] + 100 + border_thickness -1)],
                    outline=border_color, width=border_thickness)
        card.paste(profile_picture, profile_position, mask=profile_picture)
        border_color = (150, 150, 150, 255)  # Black border color
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=border_color, width=border_thickness)
        
        # Draw username
        font = ImageFont.truetype("arialbd.ttf", 30)
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        level_font = ImageFont.truetype("arial.ttf", 15)
        draw.text((5, 5), f"{username}", fill="white", font=font, stroke_width=2, stroke_fill=(20,20,20))
        draw.text((8, 40), f"The {title}", fill="white", font=font_title,stroke_width=2, stroke_fill=(20,20,20))

        #Calculate level text widths
        level_text = f"{level}"
        level_text_width = len(level_text) * 6
        level_text = "Level " + level_text 
        level_size = 45
        progress_width = int(((xp / total_xp) * 100) / 100 * 270)
        
        # Draw level bar and texts
        draw.text((12, 83), f"{xp} / {total_xp} XP", fill="white", font=level_font, stroke_width=2, stroke_fill=(20,20,20))
        draw.text((280 - (level_size + level_text_width), 83), level_text, fill="white", font=level_font, stroke_width=2, stroke_fill=((20,20,20)))
        draw.rectangle([(10, 100), (280, 110)], fill=(20,20,20), outline=(20,20,20))
        draw.rectangle([(10, 100), (10 + progress_width, 110)], fill=(0, 191, 255), outline=(20,20,20))
        """
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
        card.save(output_path)
 
   
    async def level_card(self, member):
        # Get the username and profile picture of the Discord user
        
        username = (str(member.display_name)).upper()
        channel = self.bot.get_channel(int(1256290545865592965))
        
        if member:
            thumbnail_url = str(member.avatar.url)
        else:
            await channel.send("Failed to retrieve member information.")
            return

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

            needed_xp = get_xp_needed(level)

            background, header, title, color = get_user_profile_names(member.id)

            output_path = "profile_card.png"

            print(xp, needed_xp, title, level)
           
            credits = get_user_credits(member.id)
            timespent = get_time_spent(member.id)
            last_seen = get_last_seen(member.id)
            badges = get_all_user_badges(member.id)
            #last_seen = "FIX ME"
            print(f"username: {username}, level: {level}, xp: {xp}, needed_xp: {needed_xp}, background: {background}, header: {header}, color: {color}, credits: {credits}, title: {title}, timespent: {timespent}, last_seen: {last_seen}, badges: {badges}, profile_picture_path: {profile_picture_path}, output_path: {output_path}")
            #await self.create_profile_card(username, member, level, xp, needed_xp, background, header, color, credits, title, timespent, last_seen, badges, profile_picture_path, output_path)
            await self.create_level_card(username, level, xp, needed_xp,header, profile_picture_path, output_path, title, color)

            # Send the profile card image to the Discord channel
            await channel.send(file=discord.File(output_path))
            
            # Clean up the temporary profile picture file
            os.remove(profile_picture_path)
        else:
            await channel.send("Failed to download the profile picture.")

    @commands.command()
    async def profile_card(self, ctx):
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
            await self.create_profile_card_2(username, level, xp, total_xp, profile_picture_path, output_path, title)

            # Send the profile card image to the Discord channel

            #embed = discord.Embed(title="PROFILE", description="") 
            file = discord.File(output_path)

            await ctx.send( file=file)
            #await ctx.send(file=discord.File(output_path))
            
            # Clean up the temporary profile picture file
            os.remove(profile_picture_path)
        else:
            await ctx.send("Failed to download the profile picture.")

    async def get_member_by_id(self, user_id):
        guild = self.bot.get_guild(1226714258117496922)
        if guild:
            member = guild.get_member(user_id)
            if member:
                return member
        return None
    
    async def change_role(self, user_id, level):
        if (level) % 5 == 0:
           
            level_roles = {
                "0": ["Novice", self.config["levelup"]["Novice"]],
                "5": ["Apprentice", self.config["levelup"]["Apprentice"]],
                "10": ["Adept", self.config["levelup"]["Adept"]],
                "15": ["Journeyman", self.config["levelup"]["Journeyman"]],
                "20": ["Explorer", self.config["levelup"]["Explorer"]],
                "25": ["Pathfinder", self.config["levelup"]["Pathfinder"]],
                "30": ["Vanguard", self.config["levelup"]["Vanguard"]],
                "35": ["Sentinel", self.config["levelup"]["Sentinel"]],
                "40": ["Warrior", self.config["levelup"]["Warrior"]],
                "45": ["Champion", self.config["levelup"]["Champion"]],
                "50": ["Knight", self.config["levelup"]["Knight"]],
                "55": ["Guardian", self.config["levelup"]["Guardian"]],
                "60": ["Hero", self.config["levelup"]["Hero"]],
                "65": ["Veteran", self.config["levelup"]["Veteran"]],
                "70": ["Commander", self.config["levelup"]["Commander"]],
                "75": ["Master", self.config["levelup"]["Master"]],
                "80": ["Legend",  self.config["levelup"]["Legend"]],
                "85": ["Sage", self.config["levelup"]["Sage"]],
                "90": ["Mythic", self.config["levelup"]["Mythic"]],
                "95": ["Heroic", self.config["levelup"]["Heroic"]],
                "100": ["Elder", self.config["levelup"]["Elder"]],
            }
           
            
            new_role, id = level_roles[str(level)]
            old_role, old_id = level_roles[str(level)-5]
            log("LEVEL", f"{self.get_username(user_id)} Accended from {old_role} to {new_role}")
          
            member = await self.get_member_by_id(user_id)
            role = member.guild.get_role(id)
            await member.add_roles(role)
            try:
                old_role = member.guild.get_role(old_id)
                await member.remove_roles(old_role)
            except:
                log("LEVEL", f"Failed to remove role {old_role}")
    
    async def level_up(self, user_id, xp):
        log("LEVEL", f"User {user_id} has leveled up! Current XP: {xp}")
        member = await self.get_member_by_id(user_id)
       
        user_data = get_user_data(user_id)
        random_image = generate_random_number(31)



        #check to see if level is a multple of 5
        
     

        file = discord.File(f'images/levelup/{random_image}.png')
        file2 = discord.File(f'images/levelup/{1}.png')
        thumbnail_url = str(member.avatar.url)
        channel = self.bot.get_channel(int(self.config['LEVEL_ID']))
        #channel = member.guild.get_channel(self.config['LEVEL_ID'])
        #channel = member.guild.get_channel(1074560208807940217)
        if channel:
            embed = discord.Embed(
                title=f"{member.display_name} Is Level {user_data[4]}!",
                description=f"{member.mention} You've Accumulated {user_data[3]} Total XP!",
                color=discord.Color.blue(),
                timestamp=get_time()
            )
            embed.set_author(name="LEVEL UP", icon_url=f"attachment://{file2.filename}")
            embed.set_thumbnail(url=f"attachment://{file.filename}")
        
            embed.set_footer(text="Level up to earn better rewards!")
            
            profile_picture_path = "level_temp_profile_picture.png"
        
            # Download the profile picture from the URL and save it to a temporary file
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                with open(profile_picture_path, "wb") as f:
                    f.write(response.content)

            # Get user header card data
            output_path = "level_card.png"
            username = (str(member.display_name)).upper()
            xp = get_user_xp(member.id) 
           
            level = get_level(xp)
            await self.change_role(user_id, level)

            xp = xp - get_xp_needed(level - 1)
            needed_xp = get_xp_needed(level) - get_xp_needed(level - 1)
            background, header, title, color = get_user_profile_names(member.id)
            file3 = discord.File(f"{output_path}", filename=f"{output_path}")
            embed.set_image(url=f"attachment://{output_path}")
            await self.create_level_card(username, level, xp, needed_xp,header, profile_picture_path, output_path, title, color)
            await channel.send(embed=embed, files=[file, file2, file3])
        else:
            print(f"Channel with ID {self.config["LEVEL_ID"]} not found.")
    
    async def old_level_up(self, user_id, xp):
        # Get the username and profile picture of the Discord user
        channel = self.bot.get_channel(1226714258721603617)
        member = await self.get_member_by_id(user_id)
       
        username = (str(member.display_name)).upper()
        
        if member:
            thumbnail_url = str(member.avatar.url)
        else:
            await channel.send("Failed to retrieve member information.")
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
            await self.create_level_card(username, level, xp, total_xp, profile_picture_path, output_path, title)

            # Send the profile card image to the Discord channel
            await channel.send(file=discord.File(output_path))
            
            # Clean up the temporary profile picture file
            os.remove(profile_picture_path)
        else:
            await channel.send("Failed to download the profile picture.")

    

async def setup(bot, config):
    await bot.add_cog(levelup(bot, config))