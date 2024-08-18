"""
Database Setup

This script is used to create the database and tables for the application. 
"""
import sqlite3
import json
import os
from backend.common.common import log

def create_user_table(path):
    log("[DATABASE]", "Creating user data table...")
    conn = sqlite3.connect(path + "/user_data.db")
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
    log("USER", "User data table created.")
    return True

def create_table_renown(path):
    log("[DATABASE]", "Creating renown table...")
    conn = sqlite3.connect(path)
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
    log("[DATABASE]", "Renown Table created.")

def create_persistant_views(path):
    log("[DATABASE]", "Creating renown table...")
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS views (
            view_id TEXT PRIMARY KEY,
            view_registration TEXT,
            channel_id INTEGER,
            timeout_date INTEGER,
            disabled INTEGER,
            reward INTEGER,
            catagory TEXT
        )
    ''')
    conn.commit()
    log("[DATABASE]", "Persistant Table created.")
    return True


def create_games_table(path):
    conn = sqlite3.connect("backend/databases/games.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
                    user_id INTEGER,
                    game_name TEXT,
                    game_description TEXT,
                    game_status TEXT,
                    thread_id INTEGER,
                    guess_1 TEXT,
                    guess_2 TEXT,
                    guess_3 TEXT,
                    guess_4 TEXT,
                    guess_5 TEXT,
                    guess_6 TEXT,
                    guess_7 TEXT,
                    guess_8 TEXT,
                    guess_9 TEXT,
                    guess_10 TEXT,
                    game_lockouts TEXT,
                    guesses INTEGER,
                    champion TEXT         
                )''')
    conn.commit()
    conn.close()
    return True
    

def database_setup(path):
    create_user_table(path)
    create_table_renown(path + "/renown.db")
    create_persistant_views(path + "/views.db")
    create_games_table(path + "/games.db")
    return True



