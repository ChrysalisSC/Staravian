import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View


from backend.common.common import log
import requests 
import random
import typing
import sqlite3
from PIL import Image, ImageDraw, ImageFont
import re
import os

# GAME 1
class LoLGuessingGame:
    def __init__(self):
        self.champions = ['Aatrox', 'Ahri', 'Akali', 'Akshan', 'Alistar', 'Amumu', 'Anivia', 'Annie', 'Aphelios', 'Ashe', 'AurelionSol', 'Azir', 'Bard', 'Belveth', 'Blitzcrank', 'Brand', 'Braum', 'Briar', 'Caitlyn', 'Camille', 'Cassiopeia', 'Chogath', 'Corki', 'Darius', 'Diana', 'Draven', 'DrMundo', 'Ekko', 'Elise', 'Evelynn', 'Ezreal', 'Fiddlesticks', 'Fiora', 'Fizz', 'Galio', 'Gangplank', 'Garen', 'Gnar', 'Gragas', 'Graves', 'Gwen', 'Hecarim', 'Heimerdinger', 'Hwei', 'Illaoi', 'Irelia', 'Ivern', 'Janna', 'JarvanIV', 'Jax', 'Jayce', 'Jhin', 'Jinx', 'Kaisa', 'Kalista', 'Karma', 'Karthus', 'Kassadin', 'Katarina', 'Kayle', 'Kayn', 'Kennen', 'Khazix', 'Kindred', 'Kled', 'KogMaw', 'KSante', 'Leblanc', 'LeeSin', 'Leona', 'Lillia', 'Lissandra', 'Lucian', 'Lulu', 'Lux', 'Malphite', 'Malzahar', 'Maokai', 'MasterYi', 'Milio', 'MissFortune', 'MonkeyKing', 'Mordekaiser', 'Morgana', 'Naafiri', 'Nami', 'Nasus', 'Nautilus', 'Neeko', 'Nidalee', 'Nilah', 'Nocturne', 'Nunu', 'Olaf', 'Orianna', 'Ornn', 'Pantheon', 'Poppy', 'Pyke', 'Qiyana', 'Quinn', 'Rakan', 'Rammus', 'RekSai', 'Rell', 'Renata', 'Renekton', 'Rengar', 'Riven', 'Rumble', 'Ryze', 'Samira', 'Sejuani', 'Senna', 'Seraphine', 'Sett', 'Shaco', 'Shen', 'Shyvana', 'Singed', 'Sion', 'Sivir', 'Skarner', 'Smolder', 'Sona', 'Soraka', 'Swain', 'Sylas', 'Syndra', 'TahmKench', 'Taliyah', 'Talon', 'Taric', 'Teemo', 'Thresh', 'Tristana', 'Trundle', 'Tryndamere', 'TwistedFate', 'Twitch', 'Udyr', 'Urgot', 'Varus', 'Vayne', 'Veigar', 'Velkoz', 'Vex', 'Vi', 'Viego', 'Viktor', 'Vladimir', 'Volibear', 'Warwick', 'Xayah', 'Xerath', 'XinZhao', 'Yasuo', 'Yone', 'Yorick', 'Yuumi', 'Zac', 'Zed', 'Zeri', 'Ziggs', 'Zilean', 'Zoe', 'Zyra']
        #self.load_champions()
        self.champions_dir = "images/splash"

    def load_champions(self):
        versions_resp = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
        versions = versions_resp.json()
        latest_version = versions[0]

        champions_resp = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json')
        data = champions_resp.json()
        self.champions = list(data['data'].keys())
        print(self.champions)
        
        #print(self.champions)
        

    def get_random_champion(self):
        return random.choice(self.champions)

    def get_champion_image_url(self, champion):
        return f'https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion}_0.jpg'

    
    def download_image(self, champion):
        image_url = self.get_champion_image_url(champion)
        response = requests.get(image_url)
        if response.status_code == 200:
            file_path = os.path.join(self.champions_dir, f'{champion}_0.jpg')  # Example path
            print(file_path)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path
        else:
            raise Exception(f"Failed to open image for champion {champion}")

    
def add_space_between_capitals(champion_name):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', champion_name)
        

def crop_image(champion, num_guesses):
    image_path = f'images/splash/{champion}_0.jpg'
    img = Image.open(image_path)
    print("Cropping image ", image_path, " with ", num_guesses, " guesses")

    # Determine the crop area based on the number of guesses
    width, height = img.size
    crop_percentage = min(100, 10 + num_guesses * 5)  # Increase by 5% every guess, max 100%
    crop_width = int(width * crop_percentage / 100)
    crop_height = int(height * crop_percentage / 100)

    # Calculate the center coordinates for cropping
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    right = left + crop_width
    bottom = top + crop_height

    # Crop the image
    cropped_img = img.crop((left, top, right, bottom))

    # Resize the cropped image to the original dimensions of the champion image
    cropped_img = cropped_img.resize((width, height))

    cropped_img_path = f'images/cropped_champs/{champion}_cropped.jpg'
    cropped_img.save(cropped_img_path)

    return cropped_img_path

def update_image_path(user_id, champion, num_guesses):
    # Update the image path based on the number of guesses
    return crop_image(champion, num_guesses)

#GAME 2



class GameButton(Button):
    def __init__(self, label, style, game_function, user_id, thread):
        super().__init__(label=label, style=style)
        self.game_function = game_function
        self.user_id = user_id
        self.thread = thread

    async def callback(self, interaction: discord.Interaction):
       
        await interaction.response.defer()
        await self.game_function(self.user_id, self.thread)

class Games(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.guessing_game = LoLGuessingGame()
        central_cog = self.bot.get_cog("Central")
        if central_cog:
            central_cog.register_view("games_view", self.create_game_view)
 
    async def start_game1(self, user_id, thread):
        champion = self.guessing_game.get_random_champion()
        image_path = self.guessing_game.download_image(champion)
        print(champion)
        # Crop the image
        image_path = f'images/splash/{champion}_0.jpg'
        cropped_image_path = crop_image(champion, 0)  # 0 guesses initially

         # Check if the game session already exists for this user_id
        conn = sqlite3.connect("backend/databases/games.db")
        c = conn.cursor()
        c.execute('''SELECT * FROM games WHERE user_id = ? AND game_name = ?''', (user_id, 'league_image_guess_game'))
        existing_game = c.fetchone()

        if existing_game:
            # Update the existing game session
            c.execute('''UPDATE games 
                        SET game_description = ?, game_status = ?, thread_id = ?, guesses = ?, champion = ?
                        WHERE user_id = ? AND game_name = ?''',
                    ('league_image_guess_game', 'active', thread.id, 0, champion, user_id, 'league_image_guess_game'))
        else:
            # Insert a new game session
            c.execute('''INSERT OR REPLACE INTO games 
             (user_id, game_name, game_description, game_status, thread_id, guesses, champion)
             VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, 'league_image_guess_game', 'league_image_guess_game', 'active', thread.id, 0, champion))

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="Its Time To Guess the League Of Legonds Champion!",
            description="Guess the champion from the list below.\n Use /guess to make a guess.",
            color=0x000000
        )
        file = discord.File(cropped_image_path, filename="image.jpg") 
        embed.set_image(url=f"attachment://image.jpg")

        # for chamption in self.champions
        count = 0
        champion_names = ""
        

        for champ in self.guessing_game.champions:
            champion = champ.split(" ")[0]
            champion = add_space_between_capitals(champion)
            champion_names += f"{champion}, "
            count +=1
            if count == 10:
                count = 0
                #champion_names += "\n"

        champion1 = champion_names[:len(champion_names)//2+8]
        champion2 = champion_names[len(champion_names)//2+8:]
        embed.add_field(name="Champions", value=f"{champion1}", inline=False)
        embed.add_field(name="", value=f"{champion2}", inline=False)

       


        # Send the first cropped image
        await thread.send(file=file, embed=embed)

    async def start_game2(self, user_id, thread):
        await thread.response.send_message("Starting Game 2!")

    async def start_game3(self,user_id, thread):
        await thread.response.send_message("Starting Game 3!")

    
    async def start_games(self, user_id, thread):
        # Create the embed
        embed = discord.Embed(title="Game Selector", description="Choose a game to start:", color=0xffffff)
        embed.add_field(name="SPLASH GUESS", value="Guess The league of legonds champion from their splash art", inline=False)
        embed.add_field(name="Game 2", value="Start Game 2", inline=False)
        embed.add_field(name="Game 3", value="Start Game 3", inline=False)

        # Create the buttons
        button1 = GameButton(label="SPLASH GUESS", style=discord.ButtonStyle.primary, game_function=self.start_game1, user_id=user_id, thread=thread)
        button2 = GameButton(label="Start Game 2", style=discord.ButtonStyle.primary, game_function=self.start_game2, user_id=user_id, thread=thread)
        button3 = GameButton(label="Start Game 3", style=discord.ButtonStyle.primary, game_function=self.start_game3, user_id=user_id, thread=thread)

        # Create a view and add the buttons to the view
        view = View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)

        # Send the embed with the buttons
        type(thread)
        if isinstance(thread, discord.Thread):
            await thread.send(embed=embed, view=view)
        else:
            #get thread from id
            thread = self.bot.get_channel(thread)
            await thread.send(embed=embed, view=view)

    def create_game_view(self, view_identifier):
        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Go To Games",
            custom_id=view_identifier,
        )
        view.add_item(button)

        async def button_callback(interaction):
            ThreadManager = self.bot.get_cog("ThreadManager")
            if ThreadManager is not None:
                thread = await ThreadManager.create_thread(
                    self.config["GAMES_ID"], "Games", 360, 600, interaction.user
                )
                if thread:
                    await interaction.response.send_message(
                        f"The Games Thread has opened up for you", ephemeral=True
                    )
                    await self.start_games(interaction.user.id, thread)
                else:
                    await interaction.response.send_message(
                        "You already have an open thread", ephemeral=True
                    )
        button.callback = button_callback
        return view
    
    @commands.command()
    async def games(self, ctx):
        view_identifier = f"game_view"
        view = self.create_game_view(view_identifier)
        #self.save_view_state(view_identifier)

        embed = discord.Embed(title="Welcome to the GAMES!", description="Step into the Tavern, make it your own, and let your profile tell the story of your journey!", color=0xFFFFFF)
        #embed.add_field(name="Profile", value="The Tavern is your go-to destination for customizing your profile and showcasing your achievements. Here, you can personalize your avatar, update your profile details, and flaunt the buffs and badges you've collected on your adventures.", inline=False)
        #embed.add_field(name="Customize Your Profile", value=" Tailor your profile to reflect your unique style. Choose from a variety of styles, backgrounds, and themes to create a look that stands out.", inline=False)
        #embed.add_field(name="Showcase Your Achievements", value="Display your accomplishments with pride. Whether you've conquered a dungeon, completed a quest, or earned a special badge, the Tavern is the perfect place to show off your victories.", inline=False)

        file = discord.File("images/game_icon.png", filename="game_icon.png")
        embed.set_image(url="attachment://game_icon.png")
        channel = self.bot.get_channel(int(self.config["GAMES_ID"]))

        central_cog = self.bot.get_cog("Central")
        if central_cog:
            await central_cog.add_view_to_database(view_identifier,"games_view", int(self.config["GAMES_ID"]), category="Games")
        else:
            log("[TAVERN]", "Central cog not found. View not added to database.")
        await channel.send(embed=embed, view=view, file=file)


    @app_commands.command(
        name="guess",
        description="Make a Guess!"
    )
    async def guess(self, interaction: discord.Integration, guess: str):
        user_id = interaction.user.id

        # Retrieve the game session
        conn = sqlite3.connect("backend/databases/games.db")
        c = conn.cursor()
        c.execute('''SELECT * FROM games WHERE user_id = ? AND game_status = 'active' ''', (user_id,))
        game = c.fetchone()
        conn.close()

        #check to see if interaction is in same channel as thread
        print("guess", guess )
        try:
            if interaction.channel.id != game[4]:
                await interaction.response.send_message("Please make your guess in the game thread.", ephemeral=True)
                return
        except:
            await interaction.response.send_message("Error, game over.", ephemeral=True)
            return


        if not game:
            await interaction.response.send_message("No active game found for your user.", ephemeral=True)
            return
        if game[1] == "league_image_guess_game":
            await self.league_image_guess_game(game, interaction, guess)
            return
        else:
            await interaction.response.send_message("Invalid game type.", ephemeral=True)
            return
    
    async def league_image_guess_game(self, game, interaction, guess):
        # set the game to completed if 10 guesses have been made
   

        user_id = interaction.user.id
        
        
        champion = game[17]
        print(add_space_between_capitals(champion.lower()))
        print(guess.lower())

        if guess.lower()== add_space_between_capitals(champion.lower()):
            #await interaction.response.send_message('Correct! Well done.')
            #set the game to the original image
            image_path = f'images/splash/{champion}_0.jpg'
            file = discord.File(image_path, filename="image.jpg")
            embed = discord.Embed(
                title="Correct Guess!",
                description="You have guessed the champion correctly!",
                color=0x000000
            )
            embed.set_image(url=f"attachment://image.jpg")
            await interaction.response.send_message(file=file, embed=embed)

            
            
            print(user_id, game[4])
            await self.start_games(user_id, game[4])
            


            game_completed = True
        else:
            game_completed = False

        # Update the game session with the guess and status
        conn = sqlite3.connect("backend/databases/games.db")
        c = conn.cursor()
        num_guesses = game[16]
        guess_col = f'guess_{num_guesses+1}'
        c.execute(f'''UPDATE games SET {guess_col} = ? WHERE user_id = ? AND game_status = 'active' ''',
                    (guess, user_id))
        c.execute('''UPDATE games SET guesses = guesses + 1 WHERE user_id = ? AND game_status = 'active' ''',
                    (user_id,))
        if game_completed:
            c.execute('''UPDATE games SET game_status = 'completed', game_name = NULL WHERE user_id = ? AND game_status = 'active' ''',
                    (user_id,))
        conn.commit()
        conn.close()

        # Update and send the cropped image based on the number of guesses
        if not game_completed and num_guesses+1 < 10:
            embed = discord.Embed(
                title="Inccorect Guess! Try Again!",
                description="Use /guess to make a guess.",
                color=0x000000
            )
            #for each guess that is not null, add a field to the embed
            guess_text = ""
            for i in range(0, num_guesses+1):
                #guess_col = f'guess_{i}'
                if i == num_guesses:
                    guess_text += f"Guess {i+1}: {guess}\n"
                else:
                    guess_text += f"Guess {i+1}: {game[5 + i]}\n"
               


            embed.add_field(name=f"Incorrect Guesses:", value=f"{guess_text}", inline=False)
            cropped_image_path = update_image_path(user_id, champion, num_guesses+1)
            file = discord.File(cropped_image_path, filename="image.jpg") 
            embed.set_image(url=f"attachment://image.jpg")
            await interaction.response.send_message(file=file, embed=embed)
        if game_completed:
            return
        else:
        
            conn = sqlite3.connect("backend/databases/games.db")
            c = conn.cursor()
            c.execute('''UPDATE games SET game_status = 'completed', game_name = NULL WHERE user_id = ? AND game_status = 'active' ''',
                    (user_id,))
            conn.commit()
            conn.close()
            embed = discord.Embed(
                title="Game Over!",
                description="You have made 10 guesses. The correct answer was: " + champion,
                color=0x000000
            )
            image_path = f'images/splash/{champion}_0.jpg'
            file = discord.File(image_path, filename="image.jpg")
            embed.set_image(url=f"attachment://image.jpg")
            
            await interaction.response.send_message(file=file, embed=embed)
            return
            

async def setup(bot, config):
    #name of your log(name of cog, print_info)
    log("EXAMPLE", "Setting up Example cog...")
    await bot.add_cog(Games(bot, config))
   

