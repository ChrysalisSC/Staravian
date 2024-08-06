from typing import Any
import discord
from discord.ext import commands
from discord import app_commands

from common import log
import time
import datetime

from backend.users import *
from backend.buffs import *
from backend.renown import *


def get_data_for_backgrounds():
    with open("shared_config/profile_data.json", "r") as f:
        data = json.load(f)
    f.close()
    return data

class ProfileDropdown(discord.ui.Select):
    def __init__(self, member, data, backgrounds):
        self.member = member
        self.data = data
        self.backgrounds = backgrounds
 
        options = [
             discord.SelectOption(label=f"{data['backgrounds'][background]['name']}", value=background) for background in self.backgrounds
        ]
        super().__init__(placeholder="Select a background", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_background = self.values[0]
      
        current_background, current_header, current_title, current_color = get_user_profile(self.member.id)

        if selected_background != current_background:
            set_background(self.member.id, selected_background)
            await interaction.response.send_message(f"Profile updated with Background: {selected_background}", ephemeral=True)
        else:
            await interaction.response.send_message("No changes made to the profile.", ephemeral=True)

class myselectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MySelect())

class MySelect(discord.ui.Select):
    def __init__(self):
        renown_tracks = [
            "corn",
            "meme",
            "world"
        ]
        options = [
            discord.SelectOption(label=track, value=track) for track in renown_tracks
        ]
        super().__init__(placeholder='Choose an option...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await set_selected_track(interaction.user.id, self.values[0])
        await interaction.response.send_message(f'Renown Track Changed to {self.values[0]}')


class HeaderDropdown(discord.ui.Select):
    def __init__(self, member, data, headers):
        self.member = member
        self.data = data
        self.headers = headers
      
        options = [
            discord.SelectOption(label=f" {data['headers'][header]['name']}", value=header) for header in self.headers
        ]
        super().__init__(placeholder="Select a header", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_header = self.values[0]
        current_background, current_header, current_title, current_color = get_user_profile(self.member.id)
        
        if selected_header != current_header:
            set_header(self.member.id, selected_header)
            await interaction.response.send_message(f"Profile updated with Header: {selected_header}", ephemeral=True)
        else:
            await interaction.response.send_message("No changes made, Your current background is the same", ephemeral=True)

class ColorDropdown(discord.ui.Select):
    def __init__(self, member, data, colors):
        self.member = member
        self.data = data
        self.colors = colors
        options = [
            discord.SelectOption(label=f"{data['colors'][color]['name']}", value=color) for color in self.colors
        ]
        super().__init__(placeholder="Select a color", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_color = self.values[0]
        current_background, current_header, current_title, current_color = get_user_profile(self.member.id)
        
        if selected_color != current_color:
            set_color(self.member.id, selected_color)
            await interaction.response.send_message(f"Profile updated with Color: {selected_color}", ephemeral=True)
        else:
            await interaction.response.send_message("No changes made to the profile.", ephemeral=True)

class TitleDropdown(discord.ui.Select):
    def __init__(self, member,data, titles):
        self.member = member
        self.data = data
        self.titles = titles

      
        options = [
            discord.SelectOption(label=f"{data['titles'][title]['name']}", value=title) for title in self.titles
        ]
        super().__init__(placeholder="Select a title", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_title = self.values[0]
        current_background, current_header, current_title, current_color = get_user_profile(self.member.id)
        
        if selected_title != current_title:
            set_title(self.member.id, selected_title)
            await interaction.response.send_message(f"Profile updated with Title: {selected_title}", ephemeral=True)
        else:
            await interaction.response.send_message("No changes made to the profile.", ephemeral=True)

class BadgeSelection(discord.ui.Select):
    def __init__(self, member, data, badges):
        self.member = member
        self.data = data
        self.badges = badges

        options = [
            discord.SelectOption(label=f"{self.data[badge['badge']]['name']}", value=f"{badge['badge']}") for badge in self.badges
        ]
        super().__init__(placeholder="Select badges", options=options, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        selected_badges = self.values
        current_badges = get_all_user_badges(self.member.id)  # Assuming this function retrieves current badges

        badges_added = [badge for badge in selected_badges if badge not in current_badges]
        badges_removed = [badge for badge in current_badges if badge not in selected_badges]

        # Logic to add/remove badges
        if badges_added:
            for badge_id in badges_added:
                add_badge_to_user(self.member.id, badge_id)  # Function to add badge
        if badges_removed:
            for badge_id in badges_removed:
                remove_badge_from_user(self.member.id, badge_id)  # Function to remove badge

        #embed_2 = discord.Embed(title="Badge Selection", color=0x00ff00)

        #if badges_added:
        #    added_str = "\n".join([f"**Added Badge:** {self.badge_data[badge['badge']]['name']}\n**Description:** {self.data['badges'][badge_id]['description']}" for badge_id in badges_added])
        #    embed_2.add_field(name="Added Badges", value=added_str, inline=False)
        
        #if badges_removed:
        #    removed_str = "\n".join([f"**Removed Badge:** {self.badge_data[badge['badge']]['name']}\n**Description:** {self.data['badges'][badge_id]['description']}" for badge_id in badges_removed])
        #    embed_2.add_field(name="Removed Badges", value=removed_str, inline=False)

        #await interaction.response.send_message(embed=embed_2, ephemeral=True)
        await interaction.response.send_message(f"vadges updated", ephemeral=True)
        
class ProfileView(discord.ui.View):
    def __init__(self, member, data, backgrounds, headers, titles, colors):
        super().__init__(timeout=86400)
        if len(backgrounds) != 0:
            self.add_item(ProfileDropdown(member,data, backgrounds))
        if len(headers) != 0:
            self.add_item(HeaderDropdown(member, data, headers))
        if len(colors) != 0:
            self.add_item(ColorDropdown(member, data, colors))
        if len(titles) != 0:
            if len(titles) >25:
                self.add_item(TitleDropdown(member, data, titles[:25]))
                self.add_item(TitleDropdown(member, data, titles[25:]))
            else:
                self.add_item(TitleDropdown(member, data, titles))
        

        #update this later
        #badges = get_all_user_badges(member.id)
        #with open("shared_config/badges.json", "r") as file:
            #badge_data = json.load(file)
       # file.close()

        #if len(badges) != 0:
            #self.add_item(BadgeSelection(member, badge_data,badges))

class profile_button_View(discord.ui.View):
    def __init__(self,bot, thread, member):
        super().__init__(timeout=86400)
        self.thread = thread
        self.member = member
        self.bot = bot

    @discord.ui.button(label="View Updated Profile Image", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_cog = self.bot.get_cog("Users")
        await user_cog.tavern_profile(self.thread, self.member)
        await interaction.response.send_message(f"Looking Good {self.member.name}", ephemeral=True)

class adminView(discord.ui.View):
    def __init__(self, bot, thread, member):
        super().__init__(timeout=86400)
        self.thread = thread
        self.member = member
        self.bot = bot

    async def add_all_cosmetics(self):
        # Replace this with your actual function logic
        print(f"Adding all cosmetics for {self.member.name}")
        with open ("shared_config/profile_data.json") as f:
            data = json.load(f)
        f.close()
        backgrounds = data['backgrounds']
        headers = data['headers']
        titles = data['titles']
        colors = data['colors']
        for background in backgrounds:
            add_backgrounds_to_user(self.member.id, background)
        for header in headers:
            add_header_to_user(self.member.id, header)
        for title in titles:
            add_title_to_user(self.member.id, title)
        for color in colors:
           add_color_to_user(self.member.id, color)
        await self.thread.send(f"All cosmetics added for {self.member.name}")
        
    

    @discord.ui.button(label="Add All Cosmetics", style=discord.ButtonStyle.success)
    async def add_cosmetics_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.add_all_cosmetics()
        
        #await interaction.response.send_message(f"All cosmetics added for {self.member.name}", ephemeral=True)





class Tavern(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.load_views()
       

    def load_views(self):
        # Load persistent views from the database
        if not os.path.exists('databases/views.db'):
            self.create_view_table()

        conn = sqlite3.connect('databases/views.db')
        c = conn.cursor()
        c.execute('SELECT view_identifier FROM views')
        rows = c.fetchall()
        for row in rows:
            view_identifier = row[0]
            view = self.create_tavern_view(view_identifier)
            self.bot.add_view(view)
        conn.close()
    
    def save_view_state(self, view_identifier):
        conn = sqlite3.connect('databases/views.db')
        c = conn.cursor()
        c.execute('REPLACE INTO views (view_identifier) VALUES (?)', (view_identifier,))
        conn.commit()
        conn.close()

    async def get_member_by_id(self, user_id):
        guild = self.bot.get_guild(1226714258117496922)
        if guild:
            member = guild.get_member(user_id)
            if member:
                return member
        return None
      

    async def profile_start( self, thread, user_id):
        member = await self.get_member_by_id(user_id)
        backgrounds, headers, titles, colors = get_user_collections(user_id)
        selected_background, selected_header, selected_title, selected_color = get_user_profile(user_id)
        data = get_data_for_backgrounds()
        view = ProfileView(member,data,  backgrounds, headers, titles, colors)
        embed = discord.Embed(title="Welcome To The Tavern", description="Here, you can personalize your avatar, update your profile details and check out the buffs and badges you've collected!", color=0xFFFFFF)
        embed.add_field(name="Current Background", value=data['backgrounds'][selected_background]['name'] if selected_background is not None else "None", inline=True)
        embed.add_field(name="Current Header", value=data['headers'][selected_header]['name'] if selected_header is not None else "None", inline=True)
        embed.add_field(name="", value="", inline=False)  # Spacer field
        embed.add_field(name="Current Title", value=data['titles'][selected_title]['name'] if selected_title is not None else "None", inline=True)
        embed.add_field(name="Current Color", value=data['colors'][selected_color]['name'] if selected_color is not None else "None", inline=True)
        file = discord.File("images/tavern_int.png", filename="tavern_int.png")
        embed.set_image(url="attachment://tavern_int.png")


        user_cog = self.bot.get_cog("Users")
        #embed 2 display user buffs and badges
        embed_2 = discord.Embed(title="BADGES", description="Here you can see the buffs and badges you've collected on your adventures!", color=0xFFFFFF)
        with open ("shared_config/badges.json") as f:
            badge_data = json.load(f)
        f.close()


        user_badges = get_all_user_badges(user_id)
        if user_badges:
            embed_2.add_field(name="Name", value="You have collected the following badges:", inline=False)
            text = ""
            for badge_info in user_badges:
                
                badge = badge_info.get("badge")
                timestamp = badge_info.get("timestamp")
                
                if timestamp:
                    timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                else:
                    timestamp = "Unknown"
                
                text += f"{str(badge_data[badge]['name']).upper()} - {timestamp}\n"
                text += f"{badge_data[badge]['description']}\n\n"

            embed_2.add_field(name="", value=f"```{text}```", inline=False)
            #embed_2.add_field(name=badge_data[badge]['name'], value=f"Acquired on: {timestamp}\n", inline=True)
            #embed_2.add_field(name="", value=f"{badge_data[badge]['description']}", inline=False)
        else:
            embed_2.add_field(name="No badges", value="You have not collected any badges yet.", inline=False)
       
        #embed_2.add_field(name="Badges", value="None" if len(user_badges) == 0 else "\n".join([f"{badge['name']} - {badge['description']}" for badge in user_badges]), inline=False)

        if is_admin(member.id):
            await thread.send("Admin detected", view=adminView(self.bot, thread, member))

        await thread.send(embed=embed, file=file)
        await user_cog.tavern_profile(thread, member)
        view_2 = profile_button_View(self.bot, thread, member)
        #await create_multiselect_view(thread, member.id)
        await thread.send(view=view_2)
        await thread.send(view=view)
        view_select = myselectView()

        await thread.send("select your active renown track:", view=view_select)
        await thread.send(embed=embed_2)

    def create_tavern_view(self, view_identifier):
        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Update Your Profile",
            custom_id=view_identifier,
        )
        view.add_item(button)

        async def button_callback(interaction):
            ThreadManager = self.bot.get_cog("ThreadManager")
            if ThreadManager is not None:
                thread = await ThreadManager.create_thread(
                    self.config["TAVERN_ID"], "Tavern", 360, 600, interaction.user
                )
                if thread:
                    await interaction.response.send_message(
                        f"The Tavern has opened up for you", ephemeral=True
                    )
                    await self.profile_start(thread, interaction.user.id)
                else:
                    await interaction.response.send_message(
                        "You already have an open thread", ephemeral=True
                    )
        button.callback = button_callback
        return view
    
    @commands.command()
    async def tavern(self, ctx):
        view_identifier = f"Tavern_view"
        view = self.create_tavern_view(view_identifier)
        self.save_view_state(view_identifier)

        embed = discord.Embed(title="Welcome to the Tavern!", description="Step into the Tavern, make it your own, and let your profile tell the story of your journey!", color=0xFFFFFF)
        embed.add_field(name="Profile", value="The Tavern is your go-to destination for customizing your profile and showcasing your achievements. Here, you can personalize your avatar, update your profile details, and flaunt the buffs and badges you've collected on your adventures.", inline=False)
        embed.add_field(name="Customize Your Profile", value=" Tailor your profile to reflect your unique style. Choose from a variety of styles, backgrounds, and themes to create a look that stands out.", inline=False)
        embed.add_field(name="Showcase Your Achievements", value="Display your accomplishments with pride. Whether you've conquered a dungeon, completed a quest, or earned a special badge, the Tavern is the perfect place to show off your victories.", inline=False)

        file = discord.File("images/tavern.png", filename="tavern.png")
        embed.set_image(url="attachment://tavern.png")
        channel = self.bot.get_channel(int(self.config["TAVERN_ID"]))
        await channel.send(embed=embed, view=view, file=file)
   

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





async def setup(bot, config):
    #name of your log(name of cog, print_info)
    log("TAVERN", "Setting up TAVERN cog...")
    await bot.add_cog(Tavern(bot, config))
   
