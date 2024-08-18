"""
COMMON FOLDER - COMMON.PY

This file contains the common functions that are used throughout the bot.
- Logging for the server and console,
- Time In pacific timezone,
- Random number generator,
- Open configuration file

"""

import logging
import random 
import discord
from discord.ext import commands
from datetime import datetime, timezone
import pytz
import os
import json

# Configure the logger to output to console and file
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('logs.log',  encoding='utf-8')  # Output to file
    ],
    
)
def log(file_or_cog_name, message):
    logger = logging.getLogger(file_or_cog_name)
    logger.info(message)

def generate_random_number( max_value):
        return random.randint(1, max_value)

def get_time():
    utc_now = datetime.now(timezone.utc)
    pacific_now = utc_now.astimezone(pytz.timezone('America/Los_Angeles'))
    return pacific_now

def open_config(env):
    config_file = f"config/{env}.json"

    # Check if the configuration file exists
    if os.path.exists(config_file):
        # Load and parse the configuration file
        with open(config_file, 'r') as f:
            CONFIG = json.load(f)
        f.close()
        return CONFIG
    else:
        print(f"Configuration file '{config_file}' not found.")
        return None

def get_base_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir) # this is the cog file's parent directory
    backend_dir = os.path.dirname(parent_dir)
    return backend_dir
