import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

import datetime


from backend.common.common import log
import json
from backend.utilities.users import *
from backend.utilities.renown import create_table_renown

from PIL import Image, ImageDraw, ImageFont
import os

import random
from textwrap import wrap


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

def convert_lists_to_tuples(d):
    """
    Recursively convert all lists in the dictionary to tuples.
    """
    if isinstance(d, dict):
        return {k: convert_lists_to_tuples(v) for k, v in d.items()}
    elif isinstance(d, list):
        return tuple(convert_lists_to_tuples(v) for v in d)
    else:
        return d
    
def create_gradient(size, color1, color2):
    """Create a gradient image"""
    base = Image.new('RGB', size, color1)
    top = Image.new('RGB', size, color2)
    mask = Image.new('L', size)
    mask_data = []
    for y in range(size[1]):
        for x in range(size[0]):
            mask_data.append(int(255 * (x / size[0] + y / size[1]) / 2))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def extract_colors_from_image(image_path, num_points=5):
    """Extract colors from an image along a diagonal line"""
    with Image.open(image_path) as img:
        width, height = img.size
        colors = []
        
        center_y = height // 2
        
        for i in range(num_points):
            x = int(width * i / (num_points - 1))
            y = center_y
            
            # Ensure coordinates are within image bounds
            x = min(max(x, 0), width - 1)
            y = min(max(y, 0), height - 1)
            
            color = img.getpixel((x, y))
            colors.append(color)
        
        # if colors are the same at the start and end, change color 2 to white
        if colors[0] == colors[-1]:
            colors[2] = (255, 255, 255)
            colors[1] = (0, 0, 0)
        
    return colors

def create_gradient_multiple(size, colors):
    """Create a gradient image with 5 colors"""
    total_colors = len(colors)
    base = Image.new('RGB', size, colors[0])
    
    for i in range(1, total_colors):
        top = Image.new('RGB', size, colors[i])
        mask = Image.new('L', size)
        mask_data = []
        
        for y in range(size[1]):
            for x in range(size[0]):
                progress = (x / size[0] + y / size[1]) / 2
                if progress < i/4:
                    alpha = int(255 * (progress * 4 - (i-1)))
                else:
                    alpha = 255
                mask_data.append(alpha)
        
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
    
    return base
    
def create_circular_image(image_path, size):
    # Open the image
    img = Image.open(image_path).convert("RGBA")
    
    # Resize the image to be square
    img = img.resize((size, size), Image.LANCZOS)
    
    # Create a white circular mask
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply the mask to the image
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    
    return output

def create_overlay(size, color, alpha):
    """Create a semi-transparent overlay"""
    overlay = Image.new('RGBA', size, color + (alpha,))
    return overlay

def center_text(draw, text, position, font, text_font_size=18):
    # center text given position and size
    text_font = font.font_variant(size=text_font_size)
    text_width = draw.textlength(text, font=text_font)
    text_height = text_font_size
    text_x = position[0] - text_width // 2
    text_y = position[1] - text_height // 2
    return (text_x, text_y)

def create_element(img, element_type, position, size, bg_color, border_color, title=None, text=None, font=None, title_font_size=18, text_font_size=18, text_color=None, image_path=None):
    """Create a generic element (box or circle) with optional title, text, and image"""
    draw = ImageDraw.Draw(img)
    x, y = position
    width, height = size

    # Create semi-transparent overlay
    overlay = create_overlay((width, height), bg_color, 128)

    if element_type == 'box':
        img.paste(overlay, (x, y), overlay)
        draw.rectangle([x, y, x + width, y + height], outline=border_color)
    elif element_type == 'circle':
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, width, height], fill=255)
        img.paste(overlay, (x, y), mask)
        draw.ellipse([x, y, x + width, y + height], outline=border_color)

    if text and font:
        text_font = font.font_variant(size=text_font_size)
        text_width = draw.textlength(text, font=text_font)
        text_height = text_font_size
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2
        draw.text((text_x, text_y), text, font=text_font, fill=text_color)

    if title and font:
        title_font = font.font_variant(size=title_font_size)
        title_width = draw.textlength(title, font=title_font)
        title_height = title_font_size
        title_x = x + (width - title_width) // 2
        title_y = y + height - title_height - 5  # 5 pixels padding from bottom
        draw.text((title_x, title_y), title, font=title_font, fill=text_color)

    if image_path:
        icon = Image.open(image_path).convert('RGBA')
        icon = icon.resize((int(width) - 10, int(height) - 10))  # Slightly smaller than the element
        img.paste(icon, (x + 5, y + 5), icon)

def create_element_with_wrapped_text(img, element_type, position, size, bg_color, border_color, text=None, font=None, font_size=18, text_color=None, image_path=None, padding=5):
    """Create a generic element (box or circle) with optional text or image, text wraps and aligns to top-left"""
    draw = ImageDraw.Draw(img)
    x, y = position
    width, height = size

    # Create semi-transparent overlay
    overlay = create_overlay((width, height), bg_color, 128)

    if element_type == 'box':
        img.paste(overlay, (x, y), overlay)
        draw.rectangle([x, y, x + width, y + height], outline=border_color)
    elif element_type == 'circle':
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, width, height], fill=255)
        img.paste(overlay, (x, y), mask)
        draw.ellipse([x, y, x + width, y + height], outline=border_color)

    if text and font:
        # Calculate maximum width for text
        max_text_width = width - 2 * padding

        # Wrap text
        wrapped_text = wrap(text, width=int(max_text_width / (font_size * 0.6)))  # Approximate character width

        # Draw each line of text
        text_y = y + padding
        for line in wrapped_text:
            text_width = draw.textlength(line, font=font)
            draw.text((x + padding, text_y), line, font=font, fill=text_color)
            text_y += font_size + 2  # Add a small gap between lines

    if image_path:
        icon = Image.open(image_path).convert('RGBA')
        icon = icon.resize((int(width) - 10, int(height) - 10))  # Slightly smaller than the element
        img.paste(icon, (x + 5, y + 5), icon)

def draw_rounded_rectangle(draw, position, size, radius, fill, outline=None):
    """Draw a rounded rectangle"""
    x, y = position
    width, height = size
    diameter = radius * 2

    # Draw main rectangle
    draw.rectangle([x + radius, y, x + width - radius, y + height], fill=fill)
    draw.rectangle([x, y + radius, x + width, y + height - radius], fill=fill)

    # Draw four corners
    draw.pieslice([x, y, x + diameter, y + diameter], 180, 270, fill=fill)
    draw.pieslice([x + width - diameter, y, x + width, y + diameter], 270, 360, fill=fill)
    draw.pieslice([x, y + height - diameter, x + diameter, y + height], 90, 180, fill=fill)
    draw.pieslice([x + width - diameter, y + height - diameter, x + width, y + height], 0, 90, fill=fill)

    # Draw outline
    if outline:
        draw.arc([x, y, x + diameter, y + diameter], 180, 270, fill=outline)
        draw.arc([x + width - diameter, y, x + width, y + diameter], 270, 360, fill=outline)
        draw.arc([x, y + height - diameter, x + diameter, y + height], 90, 180, fill=outline)
        draw.arc([x + width - diameter, y + height - diameter, x + width, y + height], 0, 90, fill=outline)
        draw.line([x + radius, y, x + width - radius, y], fill=outline)
        draw.line([x + radius, y + height, x + width - radius, y + height], fill=outline)
        draw.line([x, y + radius, x, y + height - radius], fill=outline)
        draw.line([x + width, y + radius, x + width, y + height - radius], fill=outline)

"""
def create_badge_element(img, position, size, bg_color, border_color, badges, badge_data_path, font_path, font_size=20, text_color="white", padding=5):
    Create a badge box element with a bold 'BADGES' title and a grid of badges
    x, y = position
    width, height = size

    # Create badge box
    badge_box = Image.new("RGBA", (width, height), bg_color + (150,))  # Semi-transparent background
    draw = ImageDraw.Draw(badge_box)

    # Draw border
    draw.rectangle([0, 0, width-1, height-1], outline=border_color)

    # Load badge data
    with open(badge_data_path, "r") as file:
        badge_data = json.load(file)

    # Draw "BADGES" title
    font = ImageFont.truetype(font_path, font_size)
    text = "BADGES"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = padding
    draw.text((text_x, text_y), text, fill=text_color, font=font)

    # Load and draw badges
    badge_size = 40  # Adjust as needed
    grid_start_y = text_y + text_height + padding
    badges_per_row = width // (badge_size + padding)
    for i, badge in enumerate(badges):
        badge_img = Image.open(f"images/badges/{badge_data[badge['badge']]['image']}").convert("RGBA")
        badge_img = badge_img.resize((badge_size, badge_size))
        row = i // badges_per_row
        col = i % badges_per_row
        badge_x = padding + col * (badge_size + padding)
        badge_y = grid_start_y + row * (badge_size + padding)
        badge_box.paste(badge_img, (badge_x, badge_y), badge_img)

    # Paste badge box onto main image
    img.paste(badge_box, (x, y), badge_box)
"""

def create_badge_element(background_img, badge_box_position, badge_box_size, badges, badge_data_path, font_path, font_size=20, text_color=(255, 255, 255), padding=5):
    # Create a new transparent image for the badge grid
    badge_grid = Image.new('RGBA', badge_box_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge_grid)
    font = ImageFont.truetype(font_path, font_size)

    # Load badge data
    with open(badge_data_path, "r") as file:
        badge_data = json.load(file)

    # Calculate grid dimensions
    grid_cols, grid_rows = 3, 5
    total_badges = grid_cols * grid_rows
    badge_width = badge_box_size[0] // grid_cols
    badge_height = badge_box_size[1] // grid_rows

    for i in range(total_badges):
        row = i // grid_cols
        col = i % grid_cols

        # Determine badge
        if i < len(badges):
            badge = badges[i]
        else:
            badge = {"badge": "default"}

        # Load badge image
        try:
            badge_img = Image.open(f"images/badges/{badge_data[badge['badge']]['image']}").convert("RGBA")
        except KeyError:
            badge_img = Image.open(f"images/badges/{badge_data['default']['image']}").convert("RGBA")

        # Resize badge image while maintaining aspect ratio
        original_width, original_height = badge_img.size
        aspect_ratio = original_width / original_height

        # Calculate new size based on aspect ratio
        target_width = badge_width - 2 * padding
        target_height = badge_height - 2 * padding

        if target_width / aspect_ratio <= target_height:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            new_width = int(target_height * aspect_ratio)
            new_height = target_height

        badge_img = badge_img.resize((new_width, new_height), Image.LANCZOS)

        # Calculate position
        x = col * badge_width + padding + (target_width - new_width) // 2
        y = row * badge_height + padding + (target_height - new_height) // 2

        # Paste badge image onto the badge grid
        badge_grid.paste(badge_img, (x, y), badge_img)

        # Draw badge text
        badge_text = badge.get('text', '')
        text_bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = x + (badge_width - text_width) // 2
        text_y = y + badge_height - text_height - padding
        draw.text((text_x, text_y), badge_text, font=font, fill=text_color)

    # Paste the badge grid onto the background image
    background_img.paste(badge_grid, badge_box_position, badge_grid)

    #paste img

def draw_text_with_shadow(image, position, text, font, text_color, shadow_color, shadow_offset):
    draw = ImageDraw.Draw(image)
    # Draw shadow
    shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
    draw.text(shadow_position, text, font=font, fill=shadow_color)
    # Draw main text
    draw.text(position, text, font=font, fill=text_color)
    

def create_new_profile_card( username, member, level, xp, needed_xp, background, header, color, credits, title, timespent, last_seen,badges, profile_picture_path, output_path):
    with open ("config/shared_config/profile_configuration.json", "r") as file:
        img_config = json.load(file)

    file.close()
    img_config = convert_lists_to_tuples(img_config)

  
    gray_color = (162, 158, 155)

    extracted_colors = extract_colors_from_image(f"images/p_headers/{header}.png", 4)
    # gradient_from_image =create_gradient((300, 200), extracted_colors)
    img = create_gradient_multiple(img_config['image_size'], extracted_colors)
    #img = create_gradient(img_config['image_size'], img_config['gradient_color1'], img_config['gradient_color2'])
    draw = ImageDraw.Draw(img)
    fonts = {name: ImageFont.truetype(path, size) for name, (path, size) in img_config['fonts'].items()}

    width = img_config['image_size'][0]
    height = img_config['image_size'][1]
    interval = 50  # Line interval
    label_offset = 5  # Offset for labels




    # Load and paste header image
    header_img = Image.open(f"images/p_headers/{header}.png")
    header_img = header_img.resize((800, 200))
    img.paste(header_img, (0, 0))


 
    # Draw XP bar
    xp_percentage = img_config['xp'] / img_config['max_xp']
    filled_width = int(img_config['xp_bar_size'][0] * xp_percentage)
    bar_radius = img_config['xp_bar_size'][1] // 2  # Set the radius to half the height for fully rounded ends

    # Draw background bar
    draw_rounded_rectangle(draw, 
                           img_config['xp_bar_position'], 
                           img_config['xp_bar_size'], 
                           bar_radius, 
                           fill=img_config['xp_bar_bg_color'], 
                           #outline=img_config['xp_bar_border_color'])
    )

    # Draw filled portion of the bar
    draw_rounded_rectangle(draw, 
                           img_config['xp_bar_position'], 
                           (filled_width, img_config['xp_bar_size'][1]), 
                           bar_radius, 
                           fill=img_config['xp_bar_fill_color'])

    # Draw XP text
    xp_text = f"{xp}/{needed_xp} XP"
    #text_width, text_height = draw.textsize(xp_text, font=fonts['xp_bar'])
    text_height =img_config['fonts']['xp_bar'][1]
    text_width = draw.textlength(xp_text,fonts['xp_bar'])
    text_position = (img_config['xp_bar_position'][0] + (img_config['xp_bar_size'][0] - text_width) // 2,
                     img_config['xp_bar_position'][1] + (img_config['xp_bar_size'][1] - text_height) // 2)
    draw.text(text_position, xp_text, font=fonts['xp_bar'], fill=img_config['xp_text_color'])
    

    profile_img = Image.open(profile_picture_path)
    profile_img = profile_img.resize(img_config['profile_size'])

    mask_large = Image.new('L', (img_config['profile_size'][0] + 2*img_config['outline_size'], img_config['profile_size'][1] + 2*img_config['outline_size']), 0)
    mask_draw = ImageDraw.Draw(mask_large)
    mask_draw.ellipse((0, 0, img_config['profile_size'][0] + 2*img_config['outline_size'], img_config['profile_size'][1] + 2*img_config['outline_size']), fill=255)
    
    mask = Image.new('L', img_config['profile_size'], 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, img_config['profile_size'][0], img_config['profile_size'][1]), fill=255)

    profile_with_outline = Image.new('RGBA', (img_config['profile_size'][0] + 2*img_config['outline_size'], img_config['profile_size'][1] + 2*img_config['outline_size']), (0, 0, 0, 0))
    profile_with_outline.paste(tuple(img_config['outline_color']), (0, 0), mask_large)
    profile_with_outline.paste(profile_img, (img_config['outline_size'], img_config['outline_size']), mask)

    img.paste(profile_with_outline, img_config['profile_position'], mask_large)

    #Draw small banner with triangular bottom
    draw.rectangle([0, 0, img_config["banner_width"], img_config["banner_height"]], fill=img_config["banner_color"])
    draw.polygon([(0, img_config["banner_height"]), 
                  (img_config["banner_width"], img_config["banner_height"]), 
                  (img_config["banner_width"] // 2, img_config["banner_height"] + 30)], 
                 fill=img_config["banner_color"])

    # Create Icon on banner
    icon_img = create_circular_image(img_config['server_icon'], img_config['icon_size'][0])
    img.paste(icon_img, img_config['icon_position'], icon_img)

   
   
    #draw.text(img_config['level_position'], "LVL " + str(img_config['level']), font=fonts['level'], fill=img_config['level_text_color'], stroke_width=1, stroke_fill=(30,30,30))
    
    # draw text level with shaodow
    draw_text_with_shadow(img, img_config['level_position'], "LVL " + str(img_config['level']), font=fonts['level'], text_color=img_config['level_text_color'], shadow_color=(30, 30, 30), shadow_offset=(3, 3))
    draw_text_with_shadow(img, img_config['username_position'], img_config['username'], fonts['username'], img_config['username_color'], (30, 30, 30), (3, 3))
    draw_text_with_shadow(img, img_config['title_position'], img_config['title'], fonts['title'], img_config['title_color'], (30, 30, 30), (3, 3))

    draw_text_with_shadow(img, img_config['desc_text_position'], "About Me:", font=fonts['desc_heading'], text_color="white", shadow_color=(30, 30, 30), shadow_offset=(3, 3))
   
    #acranum amount
    position = center_text(draw, "Traveler", img_config['acranum_position'], fonts['desc_heading'], img_config["fonts"]['desc_heading'][1])
    draw_text_with_shadow(img, img_config['acranum_amount_position'], "1000", font=fonts['desc_heading'], text_color="white", shadow_color=(30, 30, 30), shadow_offset=(3, 3))
    #acranum text
    position = center_text(draw, "Traveler", img_config['acranum_position'], fonts['desc_heading'], img_config["fonts"]['desc_heading'][1])
    draw_text_with_shadow(img, img_config['acranum_position'], "ACRANUM", font=fonts['desc_heading'], text_color="white", shadow_color=(30, 30, 30), shadow_offset=(3, 3))

    #create desciption Box
    create_element_with_wrapped_text(
        img, 
        'box', 
        img_config['description_position'], 
        img_config['description_size'], 
        img_config['description_bg_color'], 
        img_config['description_border_color'], 
        text="This is a long text that will wrap automatically if it's too long for the box.Im making it really long to see how much stuff can fit into this bot. maybe it can go on forever?", 
        font=fonts['description'], 
        font_size=img_config["fonts"]['description'][1], 
        text_color=img_config['description_text_color']
    )
    #create badges box

    #open badges
    draw_text_with_shadow(img, img_config['badge_text_position'], "Badges", font=fonts['desc_heading'], text_color="white", shadow_color=(30, 30, 30), shadow_offset=(3, 3))

    create_badge_element(
        img,
        img_config['badge_box_position'],
        img_config['badge_box_size'],
        badges,
        img_config['badge_data_path'],
        img_config['font_path'],
        font_size=img_config['badge_font_size'],
        text_color=img_config['badge_text_color'],
        padding=img_config['badge_padding']
    )

    position = center_text(draw, "Traveler", img_config['role_text_position'], fonts['desc_heading'], img_config["fonts"]['desc_heading'][1])
    draw_text_with_shadow(img, position, "Traveler", font=fonts['desc_heading'], text_color="white", shadow_color=(30, 30, 30), shadow_offset=(3, 3))



    """
    for x in range(0, width, interval):
        draw.line([(x, 0), (x, height)], fill="gray", width=1)
        for y in range(0, height, interval):
            draw.text((x + label_offset, y + label_offset), f"({x},{y})", fill="black", font= fonts['small'])

    for y in range(0, height, interval):
        draw.line([(0, y), (width, y)], fill="gray", width=1)
    """
    return img



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
        with open("config/shared_config/badges.json", "r") as file:
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
        conn = sqlite3.connect("backend/databases/user_data.db")
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
    async def setup_bot_2(self, ctx):
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:  # Skip bot accounts
                    print(f"Adding user {member.id} - {member}")
                    #if user doesnt esist in db, add them
                    await add_user(self.bot, member.id, str(member))



           


    @commands.command()
    async def profile_test(self, ctx):
        member = ctx.author
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

            xp = 750
            needed_xp = 1000

    
            background, header, title, color = get_user_profile_names(member.id)

            output_path = "profile_card.png"

            print(xp, needed_xp, title, level)
           
            credits = get_user_credits(member.id)
            timespent = get_time_spent(member.id)
            last_seen = get_last_seen(member.id)
            badges = get_all_user_badges(member.id)
            print(badges)
            #last_seen = "FIX ME"
            print(f"username: {username}, level: {level}, xp: {xp}, needed_xp: {needed_xp}, background: {background}, header: {header}, color: {color}, credits: {credits}, title: {title}, timespent: {timespent}, last_seen: {last_seen}, badges: {badges}, profile_picture_path: {profile_picture_path}, output_path: {output_path}")
            img = create_new_profile_card(username, member, level, xp, needed_xp, background, header, color, credits, title, timespent, last_seen, badges, profile_picture_path, output_path)
          
            img.save(output_path)
            file = discord.File(output_path)
            await ctx.send( file=file)
            os.remove(profile_picture_path)
        else:
            await ctx.send("Failed to download the profile picture.")
        
                
            
async def setup(bot, config):
    log("USERS", "Setting up Users cog...")
    await bot.add_cog(Users(bot, config))