import sqlite3
import json
import math
from backend.utilities.buffs import *
from backend.common.common import log, get_time
import discord
import time
import datetime
import pytz


from backend.utilities.users import *
from backend.utilities.users import *
# when A user does a specific action such as being in voice chat add a renown to them. When they hit a certain amount of renown they get a reward

#levels 1-10 100 xp need each level . 11--15 300 xp, 16-20 500 xp, 21-25 700 xp, 26-30 1000 xp, 31-35 1500 xp, 36-40 2000 xp, 41-45 2500 xp, 46-50 3000 xp

import asyncio
renown_lock = asyncio.Lock()

def create_table_renown():
    conn = sqlite3.connect("databases/renown.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS RENOWN (
            user_id INTEGER PRIMARY KEY,
            total_renown INTEGER,
            resonance INTEGER,
            resonance_level INTEGER,
            level INTEGER,
            level_level INTEGER,
            corn INTEGER,
            corn_level INTEGER,
            league INTEGER,
            league_level INTEGER,
            world INTEGER,
            world_level INTEGER,
            meme INTEGER,
            meme_level INTEGER,
            anime INTEGER,
            anime_level INTEGER,
            selected_track TEXT
            
        )
    ''')
    conn.commit()
    conn.close()

async def get_selected_track(user_id):
    conn = sqlite3.connect("databases/renown.db")
    c = conn.cursor()
    c.execute("SELECT selected_track FROM RENOWN WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return data[0]
    else:
        return "world"


async def set_selected_track(user_id, track):
    conn = sqlite3.connect("databases/renown.db")
    c = conn.cursor()
    c.execute("UPDATE RENOWN SET selected_track=? WHERE user_id=?", (track, user_id))
    conn.commit()
    conn.close()
    return True

async def add_renown_to_user(bot, user_id, renown, renown_track):
   
   async with renown_lock:
        conn = sqlite3.connect("databases/renown.db")
        c = conn.cursor()

        # Select the current total renown and specific renown track value for the user
        try:
            c.execute(f"SELECT total_renown, {renown_track} FROM RENOWN WHERE user_id=?", (user_id,))
            data = c.fetchone()
            if data is None:
                # User not found, insert new user with default values
                c.execute(f"""
                    INSERT INTO RENOWN (
                        user_id, total_renown, resonance, resonance_level, level, level_level,
                        corn, corn_level, league, league_level, world, world_level,
                        meme, meme_level, anime, anime_level, selected_track
                    ) 
                    VALUES (?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'world')
                """, (user_id,))
                conn.commit()
                # Select again after insertion
                c.execute(f"SELECT total_renown, {renown_track} FROM RENOWN WHERE user_id=?", (user_id,))
                data = c.fetchone()
        except sqlite3.Error as e:
            print("SQLite error:", e)
            conn.close()
            return

        if data:
            total_renown = data[0]
            specific_renown = data[1]

            # Check for level up based on total renown
            await check_level_up_renown(bot, user_id, specific_renown, specific_renown + renown, renown_track)

            # Update total renown and the specific renown track
            total_renown += renown
            specific_renown += renown

            c.execute(f"UPDATE RENOWN SET total_renown=?, {renown_track}=? WHERE user_id=?", (total_renown, specific_renown, user_id))
            print("UPDATED USER RENOWN:", user_id, total_renown, specific_renown)
        else:
            # Insert new user with initial renown values
            print("NEW USER:", user_id, renown, renown_track)

            c.execute(f"INSERT INTO RENOWN (user_id, total_renown, resonance, resonance_level, level, level_level, corn, corn_level, league, league_level, world, world_level, meme, meme_level, anime, anime_level, selected_track) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                      (user_id, renown, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, renown_track))
        conn.commit()
        conn.close()
        return True

def get_user_renown(user_id):
    conn = sqlite3.connect("databases/renown.db")
    c = conn.cursor()
    c.execute("SELECT total_renown FROM RENOWN WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return data[0]
    return 0

def add_renown_level_to_user(user_id, renown_track, new_level):
    print("ADDING RENOWN LEVEL TO USER", user_id, renown_track)
    conn = sqlite3.connect("databases/renown.db")
    c = conn.cursor()
    c.execute(f"UPDATE RENOWN SET {renown_track}_level=? WHERE user_id=?", (new_level, user_id))
    conn.commit()
    conn.close()
    return True

def get_renown_level(renown):
    if renown < 1000:
        return 0 + (renown // 100)
    elif renown < 3000:
        return 10 + (renown - 1000) // 300
    elif renown < 6000:
        return 15 + (renown - 3000) // 500
    elif renown < 10000:
        return 20 
    """
    elif renown < 15000:
        return 26 + (renown - 10000) // 1000
    
    elif renown < 23000:
        return 31 + (renown - 15000) // 1500
    elif renown < 33000:
        return 36 + (renown - 23000) // 2000
    elif renown < 46000:
        return 41 + (renown - 33000) // 2500
    elif renown < 61000:
        return 46 + (renown - 46000) // 3000
    else:
        return 51 + (renown - 61000) // 3500
    """
    
# functions to give rewards based on renown

async def check_level_up_renown(bot, user_id, current_xp, new_xp, renown_track):
    # Determine the current level and new level based on XP
    current_level = get_renown_level(current_xp)
    new_level = get_renown_level(new_xp)
    log("RENOWN", f"User {user_id} has {current_xp} XP and is level {current_level}. New XP: {new_xp}, New Level: {new_level}")
    
    if new_level > current_level:
        log("RENOWN", f"User {user_id} has leveled up to level {new_level} in the {renown_track} track!")
        # Call function to handle rewards for leveling up
        add_renown_level_to_user(user_id, renown_track, new_level)
        print("1")
        await handle_level_up_rewards(bot, user_id, new_level, renown_track)
        print("2")
    print("3")
    return True


async def handle_level_up_rewards(bot, user_id, level, renown_track):
    

    
    with open(f"shared_config/{renown_track}.json", "r") as file:
        rewards = json.load(file)
    print("REWARDS:", rewards)
   
    user = await bot.fetch_user(user_id)
    embed = discord.Embed(
        title=f"RENOWN MILSTONE RANK {level} REACHED",
        description=f"Congratulations **{user.display_name}**!\n You have reached a new milestone **(level {level})** in the renown {renown_track} rewards track.\n **New Rewards:**",
        color=discord.Color.blue(),
        timestamp = get_time()
    )
    embed.set_footer(text="Staravia")
    file = discord.File(f'images/server_icons/server_icon.png', filename='server_icon.png')
    embed.set_author(name="RENOWN", icon_url=f"attachment://{file.filename}")
    embed.set_thumbnail(url=f"attachment://{file.filename}")

    reward = rewards.get(str(level), {})
    print("REWARD:", reward)
    for reward_type, reward_value in reward.items():
        embed.add_field(name=f"{reward_type}".upper(), value=f"{reward_value}".upper(),inline = True)
        if reward_type == "XP":
            add_xp(bot, user_id, reward_value)
        elif reward_type == "buff":
            add_buff_to_user(user_id, reward_value)
        elif reward_type == "role":
           await add_role_to_user(bot, user_id, reward_value)
        elif reward_type == "title":
            add_title_to_user(user_id, reward_value)
        elif reward_type == "credits":
            add_user_credits(user_id, reward_value)
        elif reward_type == "background":
            add_backgrounds_to_user(user_id, reward_value)
        elif reward_type == "header":
            add_header_to_user(user_id, reward_value)
        elif reward_type == "color":
            add_color_to_user(user_id, reward_value)
        elif reward_type == "badge":
            add_badge_to_user(user_id, reward_value)
        else:
            log("ERROR", f"Reward type '{reward_type}' not recognized")
    
    try:
        await user.send(embed=embed, file=file)
    except discord.Forbidden:
        print(f"Could not send DM to user {user_id}, they might have DMs disabled.")


    
