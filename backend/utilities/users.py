import sqlite3
import json
import math
from backend.buffs import *
import datetime

from common import log, open_config, get_time
import time
import os




async def create_table():
    if os.path.isfile("databases/user_data.db"):
        return
    log("USER", "Creating user data table...")
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS USERINFO (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            credits INTEGER DEFAULT 0,
            total_xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            role_name TEXT,
            team_name TEXT,
            buffs TEXT DEFAULT '[]',
            titles TEXT DEFAULT '[]',
            selected_title TEXT,
            guild TEXT,
            daily_lockout INTEGER DEFAULT 0,
            weekly_lockout INTEGER DEFAULT 0,
            header_backgrounds TEXT DEFAULT '[]',
            set_header_background TEXT,
            profile_backgrounds TEXT DEFAULT '[]',
            selected_background TEXT,
            profile_colors TEXT DEFAULT '[]',
            selected_color TEXT,
            badges TEXT DEFAULT '[]',
            selected_badges '[]',
            timespent INTEGER DEFAULT 0,
            last_seen INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

async def add_user(bot, user_id, username):
    #get current time
    last_seen = get_time()
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO USERINFO (
            user_id, username, credits, total_xp, level, role_name,
            team_name, buffs, titles, selected_title, guild,
            daily_lockout, weekly_lockout, header_backgrounds, set_header_background,
            profile_backgrounds, selected_background, profile_colors,
            selected_color, badges, selected_badges, timespent, last_seen, is_admin
        ) VALUES (?, ?, 0, 0, 1, NULL, NULL, '[]', '["novice"]','novice', NULL, 0, 0, '["blue"]', 'blue', '["blue"]', 'blue', '["blue"]', 'blue', '[]', '[]', 0, ?, 0)
    ''', (user_id, username, last_seen))
    conn.commit()
    conn.close()
    try:
        await add_role_to_user(bot, user_id, 1258135407988703262) #fix this for prod
    except Exception as e:
        log("ERROR", f"Could not add role to user {e}")

# Get  user information database Fuctions
def get_user_xp(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data[3]

async def get_user_xp_total_and_level(bot, user_id):
    try:
        conn = sqlite3.connect("databases/user_data.db")
        c = conn.cursor()
        c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
        data = c.fetchone()
        conn.close()
    except:
        try:
            await add_user(bot, user_id, "user")
            data = get_user_data(user_id)
        except Exception:
            log("ERROR", "Could not add user")
            return

        return
    return data[3], data[4]

def get_user_credits(user_id):
    try:
        conn = sqlite3.connect("databases/user_data.db")
        c = conn.cursor()
        c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
        data = c.fetchone()
        conn.close()
    except:
       log("ERROR", "Could not add user")
    return data[2]

def get_user_data(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data

def get_user_title(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data[9]

# Get xp and credit data
def update_user_xp_and_level(user_id, new_total_xp, new_level):
    conn = sqlite3.connect("databases/user_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE USERINFO SET total_xp = ?, level = ? WHERE user_id = ?", (new_total_xp, new_level, user_id))
    conn.commit()
    conn.close()


def add_user_credits(user_id, credits):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET credits=credits + ? WHERE user_id=?", (credits, user_id))
    conn.commit()
    conn.close()

def remove_user_credits(user_id, credits):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET credits=credits - ? WHERE user_id=?", (credits, user_id))
    conn.commit()
    conn.close()

def check_and_update_credits(user_id, required_credits):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    
    # Check the current credits of the user
    c.execute("SELECT credits FROM USERINFO WHERE user_id=?", (user_id,))
    result = c.fetchone()
    
    if result is None:
        # User not found
        conn.close()
        return False

    current_credits = result[0]
    
    if current_credits >= required_credits:
        # Update credits
        c.execute("UPDATE USERINFO SET credits=credits - ? WHERE user_id=?", (required_credits, user_id))
        conn.commit()
        conn.close()
        return True
    else:
        # Not enough credits
        conn.close()
        return False

def add_title_to_user(user_id, title):
    if check_if_user_has_item(user_id, title, "titles"):
        return
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT titles FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        titles = json.loads(data[0])
        titles.append(title)
        c.execute("UPDATE USERINFO SET titles=? WHERE user_id=?", (json.dumps(titles), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, titles) VALUES (?, ?)", (user_id, json.dumps([title])))
    conn.commit()
    conn.close()
    return True

def remove_title_from_user(user_id, title):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT titles FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        titles = json.loads(data[0])
        if title in titles:
            titles.remove(title)
            c.execute("UPDATE USERINFO SET titles=? WHERE user_id=?", (json.dumps(titles), user_id))
    conn.commit()
    conn.close()
    return True

def add_backgrounds_to_user(user_id, background):
    if check_if_user_has_item(user_id, background, "backgrounds"):
        return
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT profile_backgrounds FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
   
    if data:
        backgrounds = json.loads(data[0])
        backgrounds.append(background)
        c.execute("UPDATE USERINFO SET profile_backgrounds=? WHERE user_id=?", (json.dumps(backgrounds), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, profile_backgrounds) VALUES (?, ?)", (user_id, json.dumps([background])))
    conn.commit()
    conn.close()
    return True

def remove_background_from_user(user_id, background):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT profile_backgrounds FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        backgrounds = json.loads(data[0])
        if background in backgrounds:
            backgrounds.remove(background)
            c.execute("UPDATE USERINFO SET profile_backgrounds=? WHERE user_id=?", (json.dumps(backgrounds), user_id))
    conn.commit()
    conn.close()
    return True

def add_color_to_user(user_id, color):
    if check_if_user_has_item(user_id, color, "colors"):
        return
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT profile_colors FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        colors = json.loads(data[0])
        colors.append(color)
        c.execute("UPDATE USERINFO SET profile_colors=? WHERE user_id=?", (json.dumps(colors), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, profile_colors) VALUES (?, ?)", (user_id, json.dumps([color])))
    conn.commit()
    conn.close()
    return True


def set_background(user_id, background):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET selected_background=? WHERE user_id=?", (background, user_id))
    conn.commit()
    conn.close()


def set_header(user_id, background):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET set_header_background=? WHERE user_id=?", (background, user_id))
    conn.commit()
    conn.close()

def set_color(user_id, color):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET selected_color=? WHERE user_id=?", (color, user_id))
    conn.commit()
    conn.close()

def set_title(user_id, title):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET selected_title=? WHERE user_id=?", (title, user_id))
    conn.commit()
    conn.close()

def add_header_to_user(user_id, background):
    if check_if_user_has_item(user_id, background, "headers"):
        return
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT header_backgrounds FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        backgrounds = json.loads(data[0])
        backgrounds.append(background)
        c.execute("UPDATE USERINFO SET header_backgrounds=? WHERE user_id=?", (json.dumps(backgrounds), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, header_backgrounds) VALUES (?, ?)", (user_id, json.dumps([background])))
    conn.commit()
    conn.close()
    return True

def remove_header_from_user(user_id, background):
  
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT header_backgrounds FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        backgrounds = json.loads(data[0])
        if background in backgrounds:
            backgrounds.remove(background)
            c.execute("UPDATE USERINFO SET header_backgrounds=? WHERE user_id=?", (json.dumps(backgrounds), user_id))
    conn.commit()
    conn.close()
    return True

def check_if_user_has_item(user_id, item_name, category):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
   
   
    if data is not None:
        if category == "backgrounds":
            backgrounds = json.loads(data[15])  # index 14 corresponds to 'profile_backgrounds' in the database schema
            if item_name in backgrounds:
                return True
            else:
                return False
        elif category == "headers":
            headers = json.loads(data[13])  # index 12 corresponds to 'header_backgrounds' in the database schema
            if item_name in headers:
                return True
            else:
                return False
        elif category == "titles":
            titles = json.loads(data[8])  # index 8 corresponds to 'titles' in the database schema
            if item_name in titles:
                return True
            else:
                return False
        elif category == "colors":
            colors = json.loads(data[17])  # index 16 corresponds to 'profile_colors' in the database schema
            if item_name in colors:
                return True
            else:
                return False
    else:
        return False
  
def get_name_of_item(item_id, category):
    with open("shared_config/profile_data.json", "r") as f:
        data = json.load(f)
    f.close()
    print(item_id, category)
    if category == "background":
        return data['backgrounds'][item_id]['name'], data['backgrounds'][item_id]['description']
    elif category == "header":
        return data['headers'][item_id]['name'], data['headers'][item_id]['description']
    elif category == "title":
        return data['titles'][item_id]['name'], data['titles'][item_id]['description']
    elif category == "color":
        return data['colors'][item_id]['name'], data['colors'][item_id]['description']
    else:
        return None
       



def get_level(total_xp):
    level = 1
    xp_threshold = 100
    xp_increment = 100
    
    while total_xp >= xp_threshold:
        total_xp -= xp_threshold
        level += 1
        xp_threshold += xp_increment
    
    return level

def get_xp_needed(level):
    if level is None or level < 0:
        return 1
    total_xp = 0
    xp_threshold = 100
    xp_increment = 100
    
    for lvl in range(1, level + 1):
        total_xp += xp_threshold
        xp_threshold += xp_increment
    
    return total_xp


def check_level_up(total_xp, new_total_xp, ):
    #return true or false if the user has leveled up
    old_level = get_level(total_xp)
    current_level = get_level(new_total_xp)
    log("LEVEL", f"Old Level: {old_level}, New Level: {current_level}")
    return current_level > old_level, current_level

async def add_xp(bot, user_id, xp_to_add, buff_type='XP'):
    # Get the current level and XP left over from the previous level
   
    total_xp, current_level = await get_user_xp_total_and_level(bot, user_id)

    # Calculate the total XP to add after applying buffs
    xp_to_add = get_xp_after_buffs(user_id, xp_to_add, buff_type)
 
    new_total_xp = total_xp + xp_to_add
    
    # Check if the user has leveled up
    level_up_occurred, level = check_level_up(total_xp, new_total_xp)

    if level_up_occurred:
        log("LEVEL", f"User {user_id} leveled up to level {level}")
        level_cog = bot.get_cog("levelup")
        update_user_xp_and_level(user_id, new_total_xp, level)
        await level_cog.level_up(user_id, level)
        return
        # Update the user's level in the data store
        # send level up embed
    update_user_xp_and_level(user_id, new_total_xp, level)
    return 

def update_user_xp_and_level(user_id, new_total_xp, new_level):
    conn = sqlite3.connect("databases/user_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE USERINFO SET total_xp = ?, level = ? WHERE user_id = ?", (new_total_xp, new_level, user_id))
    conn.commit()
    conn.close()

def add_time_to_user(user_id, time):
    log("USERS", f"Adding {time} seconds to user {user_id}'s time spent.")
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET timespent=timespent + ? WHERE user_id=?", (time, user_id))
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT selected_background, set_header_background, selected_title, selected_color FROM USERINFO WHERE user_id=?", (user_id,))
    profile_settings = c.fetchone()
    conn.close()

    # Return a dictionary with the user's profile settings
    return profile_settings[0], profile_settings[1], profile_settings[2], profile_settings[3]

def get_user_profile_names(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT selected_background, set_header_background, selected_title, selected_color FROM USERINFO WHERE user_id=?", (user_id,))
    profile_settings = c.fetchone()
    conn.close()
    
    with open ("shared_config/profile_data.json", "r") as f:
        data = json.load(f)
    f.close()
    
    background = data['backgrounds'][profile_settings[0]]['id']
    header = data['headers'][profile_settings[1]]['id']
    title = data['titles'][profile_settings[2]]['name']
    color = data['colors'][profile_settings[3]]['color']
   
    return background, header, title, color
    
    

def get_all_profile_data(user_id):
    # gets all the profile data for the user 
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()


def get_user_collections(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT pbackendrofile_backgrounds, header_backgrounds, titles, profile_colors FROM USERINFO WHERE user_id=?", (user_id,))
    collections = c.fetchone()
    conn.close()
    if collections is None:
        return [], [], [], []

    

    # Return a dictionary with all collections
    backgrounds = json.loads(collections[0])
    headers = json.loads(collections[1])
    titles = json.loads(collections[2])
    colors = json.loads(collections[3])
   
    return backgrounds, headers, titles, colors

def get_time_spent(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT timespent FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data[0]

def get_last_seen(user_id):
    try:
        conn = sqlite3.connect("databases/user_data.db")
        c = conn.cursor()
        c.execute("SELECT last_seen FROM USERINFO WHERE user_id=?", (user_id,))
        data = c.fetchone()
        conn.close()
    except:
        return "ERROR"
    return data[0]

def update_last_seen(user_id, time):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET last_seen=? WHERE user_id=?", (time, user_id))
    conn.commit()
    conn.close()

def update_ranks():
    # for each member in the database, update their rank in relation to each other.
    #store the data in "shared_config/ranks.json"
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT user_id, total_xp FROM USERINFO")
    data = c.fetchall()
    conn.close()
    data.sort(key=lambda x: x[1], reverse=True)
    
    ranks = {}
    for i, user in enumerate(data):
        ranks[user[0]] = i + 1
    with open("shared_config/ranks.json", "w") as f:
        json.dump(ranks, f)
    f.close()
    return 


async def add_role_to_user(bot, user_id, role_id):
    config = open_config("dev")
    try:
        # Fetch user and role objects
        user = await bot.fetch_user(user_id)
        if not user:
            log("ERROR", f"User with ID {user_id} not found.")
          
            return
        
        guild = bot.get_guild(config["GUILD_ID"])  # Replace guild_id with your guild ID
        role = guild.get_role(role_id)
        if not role:
            log("ERROR", f"Role with ID {role_id} not found.")
            return
        
        # Add role to the user
        member = guild.get_member(user.id)
        await member.add_roles(role)
        
        log("ROLE", f"Added role {role.name} to user {user.name}.")
        
    except Exception as e:
        log("ERROR", f"Error adding role to user: {e}")

def get_all_user_badges(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT badges FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return json.loads(data[0])
    return []

def add_badge_to_user(user_id, badge):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT badges FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        badges = json.loads(data[0])
        if not any(b['badge'] == badge for b in badges):
            badges.append({"badge": badge, "timestamp": int(time.time())})
            c.execute("UPDATE USERINFO SET badges=? WHERE user_id=?", (json.dumps(badges), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, badges) VALUES (?, ?)", (user_id, json.dumps([{"badge": badge, "timestamp": int(time.time())}])))
    conn.commit()
    conn.close()
    return True

def remove_badge_from_user(user_id, badge):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT badges FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        badges = json.loads(data[0])
        badges = [b for b in badges if b['badge'] != badge]
        c.execute("UPDATE USERINFO SET badges=? WHERE user_id=?", (json.dumps(badges), user_id))
    conn.commit()
    conn.close()
    return True

def get_user_selected_badges(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT selected_badges FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return json.loads(data[0])
    return []

def add_selected_badge_to_user(user_id, badge):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT selected_badges FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        selected_badges = json.loads(data[0])
        selected_badges.append(badge)
        c.execute("UPDATE USERINFO SET selected_badges=? WHERE user_id=?", (json.dumps(selected_badges), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, selected_badges) VALUES (?, ?)", (user_id, json.dumps([badge])))
    conn.commit()
    conn.close()
    return True

def remove_selected_badge_from_user(user_id, badge):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT selected_badges FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        selected_badges = json.loads(data[0])
        if badge in selected_badges:
            selected_badges.remove(badge)
            c.execute("UPDATE USERINFO SET selected_badges=? WHERE user_id=?", (json.dumps(selected_badges), user_id))
    conn.commit()
    conn.close()
    return True

def update_selected_badges(user_id, selected_badges):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET selected_badges=? WHERE user_id=?", (json.dumps(selected_badges), user_id))
    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT is_admin FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return data[0] == 1
    return False

def set_admin(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET is_admin=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def set_level(user_id, level):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET level=? WHERE user_id=?", (level, user_id))
    conn.commit()
    conn.close()

def set_xp(user_id, xp):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("UPDATE USERINFO SET total_xp=? WHERE user_id=?", (xp, user_id))
    conn.commit()
    conn.close()

       
