import discord
from discord.ext import commands
from discord import app_commands

from common import log
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont
import asyncio

# Function to create the Wordle table if it doesn't exist
def create_wordle_table():
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wordle
                 (user_id INTEGER,thread_id INTEGER, word TEXT, attempts INTEGER, guess_1 TEXT, guess_2 TEXT, guess_3 TEXT, guess_4 TEXT, guess_5 TEXT, guess_6 TEXT)''')
    conn.commit()
    conn.close()

# Function to insert user data into the Wordle table
def insert_wordle_data(user_id, thread_id, word, attempts, guesses):
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute("INSERT INTO wordle (user_id, thread_id, word, attempts, guess_1, guess_2, guess_3, guess_4, guess_5, guess_6) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, thread_id, word, attempts, *guesses, ""))
    conn.commit()
    conn.close()

# Function to retrieve user data from the Wordle table
def get_wordle_data(user_id):
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute("SELECT * FROM wordle WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data

# Function to update user data in the Wordle table
def update_wordle_data(user_id,thread_id, word, attempts, guesses):
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute("UPDATE wordle SET word=?, thread_id=?, attempts=?, guess_1=?, guess_2=?, guess_3=?, guess_4=?, guess_5=?, guess_6=? WHERE user_id=?",
              (word, thread_id, attempts, *guesses, user_id))
    conn.commit()
    conn.close()

# Function to generate a random word for Wordle
def generate_word():
    word_list = ['hello', 'world', 'python', 'discord', 'cog', 'sqlite', 'table', 'command', 'guess']
    return random.choice(word_list)

# Function to check if the guess is valid
def is_valid_guess(guess):
    return len(guess) == 5 and guess.isalpha()

# Function to generate a random word for Wordle
def generate_word():
    word_list = ['hello', 'world', 'guess']
    return random.choice(word_list)



# Function to check if the guess is valid
def is_valid_guess(guess):
    return len(guess) == 5 and guess.isalpha()

class Wordle(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        create_wordle_table()
        self.current_thread_ids = []
    
    @commands.command()
    async def wordle_button(self, ctx):
        view_identifier = f"Wordle_View"
        view = discord.ui.View(timeout=86400)
        button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Daily Wordle", custom_id=view_identifier)
        view.add_item(button) 

        embed = discord.Embed(title="THE DAILY WORDLE", description="TEMP DESC", color=0xFFFFFF)

        async def button_callback(interaction): 
            if interaction.user.id not in self.current_thread_ids:
                self.current_thread_ids.append(interaction.user.id)
            await self.wordle(interaction.user)

            await interaction.response.send_message("Created Thread", ephemeral=True)
            try:
                data = get_wordle_data(interaction.user.id)
                wordle_channel = self.bot.get_channel(1238627040429604864)
                thread = wordle_channel.get_thread(data[1])
                await asyncio.sleep(300)  # Wait for 1 minute
                await thread.delete()  # Delete the thread after 1 minute
            except Exception as e:
                print(e)
                print("Thread already deleted")
   
        button.callback = button_callback
        channel = self.bot.get_channel(1238627040429604864)
        await channel.send(embed=embed, view=view)

    async def wordle(self, user):
        user_id = user.id
        data = get_wordle_data(user_id)
        wordle_channel = self.bot.get_channel(1238627040429604864)
        thread = await wordle_channel.create_thread(name="Wordle Game", auto_archive_duration=60) 
        if data:
            word = data[2]
            thread_id = data[1] 
            attempts = data[3]
            previous_guesses = data[4:]  # Assign the remaining elements of data to previous_guesses
            if word == "":
                word = generate_word()
                attempts = 6
                previous_guesses = [""] * 6
                thread_id = data[1] 
                update_wordle_data(user_id,thread.id, word, attempts, previous_guesses)
                self.current_thread_ids.append(thread.id)
                message = "Let's play Wordle! You have 6 attempts to guess a 5-letter word. Use the command `!guess <word>` to make a guess."
            else:
                update_wordle_data(user_id,thread.id, word, attempts, previous_guesses)
                message = f"You are already playing Wordle with the word '{word}'. You have {attempts} attempts left."
        else:
            word = generate_word()
            attempts = 6
            previous_guesses = [""] * 5
            wordle_channel = self.bot.get_channel(1238627040429604864)
            thread = await wordle_channel.create_thread(name="Wordle Game", auto_archive_duration=60) 
            insert_wordle_data(user_id,thread.id, word, attempts, previous_guesses)
            message = "Let's play Wordle! You have 6 attempts to guess a 5-letter word. Use the command `!guess <word>` to make a guess.\n The thread will be deleted in 5 minutes."

        await thread.add_user(user) 
        await thread.send(message)

        


    @commands.command()
    async def guess(self, ctx, guess_word: str):
        user_id = ctx.author.id
        data = get_wordle_data(user_id)
        print(data)
        if not data:
            await ctx.send("You haven't started playing Wordle. Use the command `!wordle` to start a new game.")
            return

        word = data[2]
        thread_id = data[1] 
        attempts = data[3]
        previous_guesses = list(data[4:])
        if attempts <= 0:
            await ctx.send("You have no attempts left. The word was: " + word)
            return

        if not is_valid_guess(guess_word):
            await ctx.send("Invalid guess. Guess must be a 5-letter word with no spaces or special characters.")
            return

        if guess_word in previous_guesses:
            await ctx.send("You have already guessed this word. Please guess a different word.")
            return
        print(previous_guesses)
        previous_guesses[6 - attempts] = guess_word

        bulls, cows = 0, 0
        for i in range(5):
            if guess_word[i] == word[i]:
                bulls += 1
            elif guess_word[i] in word:
                cows += 1
        
        
        await self.create_wordle_grid(word, previous_guesses)

        
        
        update_wordle_data(user_id,thread_id, word, attempts - 1, previous_guesses)
        embed = discord.Embed(
            
            title=f"Wordle Game",
            description=f"",
            color=0xFFFFFF
            
        )
        file = discord.File(f'games/wordle/wordle_grid.png')
        embed.set_image(url=f"attachment://{file.filename}")
        embed.add_field(name=f"Guess: {guess_word}", value=f"Bulls: {bulls}, Cows: {cows}, Attempts left: {attempts - 1}", inline=False)
       
    
        await ctx.send(embed=embed, file =file)

        if guess_word == word:
            await ctx.send(f"Congratulations! You guessed the word '{word}' in {6 - attempts} attempts.")
            await ctx.send(f"The thread Will delete in 1 minute. Be sure to save the image of the wordle game to show off")
            wordle_channel = self.bot.get_channel(1238627040429604864)
            thread = wordle_channel.get_thread(data[1])
            update_wordle_data(user_id, '', '', 0, [""] * 6)
            await asyncio.sleep(60)  # Wait for 1 minute
            
      
            await thread.delete()  # Delete the thread after 1 minute

    @commands.command()
    async def reset_wordle(self, ctx):
        user_id = ctx.author.id
        data = get_wordle_data(user_id)
        if data:
            update_wordle_data(user_id, '', '', 6, [""] * 6)  # Clear word, reset attempts, and clear previous guesses
            await ctx.send("Wordle game has been reset. Use the command `!wordle` to start a new game.")
        else:
            await ctx.send("You are not currently playing Wordle. Use the command `!wordle` to start a new game.")

    
    async def create_wordle_grid(self, correct_word, words):
       
       
        BOX_SIZE = 40  # Size of each box in pixels
     
        MARGIN = 20  # Margin around the grid
        BG_COLOR = "white"  # Background color
        BOX_COLOR = "black"  # Box color
        LINE_WIDTH = 2  # Width of grid lines
        TEXT_COLOR = "white"  # Text color
        TEXT_FONT = ImageFont.truetype("arialbd.ttf", 30)  # Font for the text

        # Calculate image size
        image_width = 248
        image_height = 300

        # Create a new image
        image = Image.new("RGB", (image_width, image_height), color=BG_COLOR)
        draw = ImageDraw.Draw(image)

        # Draw grid lines 5 by 6
        for row in range(6):
            for col in range(5):
                x1 = MARGIN + ((BOX_SIZE + LINE_WIDTH) * col)
                y1 = MARGIN + ((BOX_SIZE + LINE_WIDTH) * row)
                x2 = x1 + BOX_SIZE 
                y2 = y1 + BOX_SIZE
                draw.rectangle([(x1, y1 + 20), (x2, y2+ 20)], fill="white", outline="black")
        
        # Manually place the text "WORDLE" at the top
        text = "WORDLE"
        WORDLE_FONT = ImageFont.truetype("fonts/Nunito/Nunito-Light.ttf", 36)  # Font for the text
        text_x = 45  # Manually adjust the x-coordinate
        text_y = 0  # Manually adjust the y-coordinate
        draw.text((text_x, text_y), text, fill="black", font=WORDLE_FONT)

        
        words = [word.upper() for word in words if word != ""]
        length = len(words)
        correct_word = correct_word.upper()
      
        if length == 0:
            image.save("games/wordle/wordle_grid.png")
            return None
        
        
        for row in range(0,length):
            for col in range(5):
                x1 = MARGIN + ((BOX_SIZE + LINE_WIDTH) * col)
                y1 = MARGIN + ((BOX_SIZE + LINE_WIDTH) * row)
                x2 = x1 + BOX_SIZE 
                y2 = y1 + BOX_SIZE
              

                # Check if the letter is in the correct word\
                #print(words[row][col], correct_word[col])
                if words[row][col] in str(correct_word):
                    # Check if it's in the correct position
                    
                    if correct_word[col] == words[row][col]:
                        box_color =	(108,169,101)
                    else:
                        box_color = (200,182,83)
                else:
                    box_color = (120,124,127)

                draw.rectangle([(x1, y1 + 20), (x2, y2+ 20)], fill=box_color, outline=BOX_COLOR)
                text = f"{words[row][col]}"
                text_width = draw.textlength(text, font=WORDLE_FONT)
                text_x = x1 + (BOX_SIZE - text_width) / 2
                text_y = y1  - 2 +  (BOX_SIZE) / 2

                draw.text((text_x, text_y), text, fill=TEXT_COLOR, font=WORDLE_FONT)
              
        # Save the image with border
        image.save("games/wordle/wordle_grid.png")
    
        return None


async def setup(bot, config):
    await bot.add_cog(Wordle(bot, config))
