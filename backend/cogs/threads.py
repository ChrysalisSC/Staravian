import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

from backend.common.common import log
import sqlite3
import random
import asyncio

descriptions = [
    "A shimmering thread of destiny unfurls for the next {minutes} minutes. Follow its path!",
    "From the depths of time, a golden thread emerges for {minutes} minutes. Let it guide you!",
    "Behold, a celestial thread materializes for the next {minutes} minutes. Weave your fate upon it!",
    "In the realm of dreams, a silver thread reveals itself for {minutes} minutes. Follow its gentle glow!",
    "A thread of magic unravels before you, lasting for {minutes} minutes. Embrace its mystical allure!",
    "From the tapestry of fate, a radiant thread emerges for {minutes} minutes. Let it illuminate!",
    "In the weave of time, a thread of possibility unfolds for {minutes} minutes. Seize the moment it presents!",
    "From the heart of the Staravb, a luminous thread appears for {minutes} minutes. Dance upon its cosmic strands!",
    "In the whispers of destiny, a thread of opportunity manifests for {minutes} minutes. Grasp it tightly!",
    "From the wellspring of existence, a vibrant thread springs forth for {minutes} minutes. Carve your mark upon it!",
    "A thread of wonderment reveals itself for the next {minutes} minutes. Let curiosity guide your exploration!",
    "Emerging from the mists of time, a thread of legend appears for {minutes} minutes. Weave your epic tale!",
    "In the realm of imagination, a thread of creativity blossoms for {minutes} minutes. Let your ideas flow!",
    "From the heart of nature, a verdant thread unfurls for the next {minutes} minutes. Connect with its vitality!",
    "A thread of inspiration ignites for **{minutes} minutes**, sparking the flames of ingenuity within you!",
    "From the forge of destiny, a fiery thread arises for the next **{minutes}** minutes. Shape your destiny with its heat!",
    "In the depths of the unknown, a mysterious thread reveals itself for **{minutes} minutes**. Explore its enigmatic path!",
    "A thread of friendship emerges for the next **{minutes} minutes**, binding hearts together in joyous harmony!",
    "From the symphony of existence, a melodic thread emerges for **{minutes} minutes**. Let its music guide your soul!",
    "In the dance of stars, a celestial thread appears for the next **{minutes} minutes**. Follow its cosmic choreography!",
    "A glimmering thread of possibility reveals itself for the next **{minutes} minutes**. Dare to chase your dreams!",
    "From the heart of the universe, a thread of cosmic energy emerges for **{minutes} minutes**. Embrace its power!",
    "In the realm of legends, a golden thread of destiny unfolds for **{minutes} minutes**. Carve your own saga!",
    "From the depths of the unknown, a thread of mystery arises for the next **{minutes} minutes**. Explore its secrets!",
    "A thread of fate appears before you, lasting for **{minutes} minutes**. Seize the moment and shape your destiny!",
    "From the misty veil of time, a shimmering thread emerges for **{minutes} minutes**. Follow its ethereal path!",
    "In the whispers of the wind, a thread of adventure reveals itself for **{minutes} minutes**. Answer its call!",
    "From the cosmic tapestry, a thread of enlightenment appears for the next **{minutes} minutes**. Seek its wisdom!",
    "A thread of hope manifests before you, lasting for **{minutes} minutes**. Let it light your way forward!",
    "In the garden of possibilities, a delicate thread of opportunity blooms for **{minutes} minutes**. Nurture it!",
    "From the depths of the ocean, a thread of serenity emerges for the next **{minutes} minutes**. Find peace within!",
    "A thread of courage materializes before you, lasting for **{minutes} minutes**. Take bold steps forward!",
    "In the dance of the fireflies, a thread of magic reveals itself for **{minutes} minutes**. Embrace its enchantment!",
    "From the realm of dreams, a thread of inspiration emerges for the next **{minutes} minutes**. Let it spark creativity!",
    "A thread of resilience appears before you, lasting for **{minutes} minutes**. Stand strong in the face of challenges!",
    "In the melody of nature, a harmonious thread reveals itself for **{minutes} minutes**. Listen to its song!",
    "From the forge of destiny, a thread of purpose emerges for the next **{minutes} minutes**. Discover your calling!",
    "A thread of friendship weaves through the air, lasting for **{minutes} minutes**. Connect with kindred spirits!",
    "In the embrace of the stars, a celestial thread reveals itself for **{minutes} minutes**. Follow its celestial path!",
    "From the depths of the forest, a thread of tranquility emerges for the next **{minutes} minutes**. Find solace within!",
    "A thread of innovation appears before you, lasting for **{minutes} minutes**. Let it guide your inventions!",
    "In the dance of the aurora, a thread of wonder reveals itself for **{minutes} minutes**. Marvel at its beauty!",
    "From the pages of history, a thread of legacy emerges for the next **{minutes} minutes**. Leave your mark!",
    "A thread of joy manifests before you, lasting for **{minutes} minutes**. Let it fill your heart with happiness!",
    "In the whispers of the ancients, a thread of wisdom reveals itself for **{minutes} minutes**. Learn from the past!",
    "From the realm of imagination, a thread of creativity emerges for the next **{minutes} minutes**. Let it inspire you!",
    "A thread of determination appears before you, lasting for **{minutes} minutes**. Pursue your goals with unwavering resolve!",
    "In the dance of the butterflies, a thread of transformation reveals itself for **{minutes} minutes**. Embrace change!",
    "From the heart of the mountains, a thread of strength emerges for the next **{minutes} minutes**. Draw power from within!",
    "A thread of laughter weaves through the air, lasting for **{minutes} minutes**. Let it lift your spirits!",
    "In the whispers of the breeze, a thread of serendipity reveals itself for **{minutes} minutes**. Embrace unexpected joys!"
]


class ThreadManager(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.thread_task.start()
        self.config = config
        self.current_thread_ids = {}
        self.user_threads = {}  # Dictionary to track user threads
        self.fish_channel = 1239321686977941687

        # Register event listener
        bot.add_listener(self.on_thread_delete, 'on_thread_delete')

    async def create_thread(
        self, channel_id, thread_name, duration, thread_extended_duration, author
    ):
        channel = self.bot.get_channel(int(channel_id))
        if channel:
            # Check if the user already has a thread in this channel
            user_channel_key = (channel_id, author.id)
            if user_channel_key in self.user_threads:
               
                return False

            # Create the thread
            thread = await channel.create_thread(
                name=thread_name, auto_archive_duration=60
            )
            self.current_thread_ids[thread.id] = duration
            self.user_threads[user_channel_key] = thread.id  # Track the thread for the user
            log("THREADS", f"Thread created: {thread.name}")
            await thread.add_user(author)

            minutes = (duration // 60) + 1
            selected_description = random.choice(descriptions).format(minutes=minutes)
            
            embed = discord.Embed(
                title= f"A Thread Appears! - {thread_name}",
                description=selected_description,
                color=0xFFFFFF,
            )
            await thread.send(embed=embed)

            # Run the thread deletion in the background
            asyncio.create_task(
                self.delete_thread_after_duration(
                    thread, duration, thread_extended_duration, author
                )
            )

            return thread
        else:
            return False

    async def delete_thread_after_duration(
        self, thread, duration, thread_extended_duration, author
    ):
        try:
            await asyncio.sleep(duration)
            while True:
                if not await self.is_thread_active(thread.id):
                    break
                
                button_pressed = False

                view_identifier = f"keep_thread_open_{thread.id}"
                view = discord.ui.View(timeout=None)
                button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="Extend Time",
                    custom_id=view_identifier,
                )
                view.add_item(button)

                embed = discord.Embed(
                    title="WARNING:",
                    description=f"THIS THREAD WILL BE DELETED IN 1 MINUTE - CLICK TO EXTEND DURATION BY {thread_extended_duration} SECONDS",
                    color=0xFFFFFF,
                )

                async def button_callback(interaction):
                    nonlocal button_pressed
                    button_pressed = True
                    await interaction.response.send_message(
                        "Thread duration extended", ephemeral=True
                    )

                button.callback = button_callback
                await thread.send(embed=embed, view=view)

                await asyncio.sleep(60)

                if button_pressed:
                    await asyncio.sleep(thread_extended_duration)
                else:
                    try:
                        if await self.is_thread_active(thread.id):
                            await thread.delete()
                            print(f"Thread deleted: {thread.name}")
                            self.current_thread_ids.pop(thread.id, None)
                            user_channel_key = (thread.parent.id, author.id)
                            self.user_threads.pop(user_channel_key, None)  # Remove the tracking entry
                        break
                    except Exception as e:
                        print(f"Thread could not be deleted: {thread.name} - ERROR {e}")
                        break

        except Exception as e:
            print(f"Error deleting thread: {e}")
            return

    async def is_thread_active(self, thread_id):
        return self.bot.get_channel(thread_id) is not None

    async def on_thread_delete(self, thread):
        print("ON THREAD DELETE!")
        if thread.id in self.current_thread_ids:
            self.current_thread_ids.pop(thread.id, None)
            for key, value in list(self.user_threads.items()):
                if value == thread.id:
                    self.user_threads.pop(key, None)
                    break

    @tasks.loop(hours=24)
    async def thread_task(self):
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            guild = self.bot.get_guild(self.config["GUILD_ID"])
            if guild:
                for channel in guild.text_channels:
                    if channel.is_thread():
                        await channel.delete()

    @thread_task.before_loop
    async def before_thread_task(self):
        await self.bot.wait_until_ready()

async def setup(bot, config):
    await bot.add_cog(ThreadManager(bot, config))
    log("THREADS", "Threads cog loaded")

