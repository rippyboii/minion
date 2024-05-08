
import discord
import asyncio
from discord.ext import commands
import random
from TOKEN import TOKEN
import secrets
import string
from discord.ui import Button, View, Modal, TextInput
from discord import ButtonStyle
from discord import TextInput 




intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True
intents.members = True

data_lock = asyncio.Lock()


bot = commands.Bot(command_prefix='!', intents=intents)


GREETINGS = ["hi", "hello", "namaste"]
RESPONSES = [
    "Seems like you have no one to play with, so Namaste there!",
    "Namaste? Anyone there? Well, I'm here for you!",
    "Looks like it's just you and me here, Namaste!",
    "Echo... Echo... Just kidding, I'm here.",
    "Lonely? Don't worry, you've got company!"
]

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    submit_channel = bot.get_channel(SUBMIT_TASK_CHANNEL_ID)
    await submit_channel.purge(limit=100)  # Clears previous messages

    # Get the category and delete all other channels within it
    category = bot.get_channel(SUBMIT_CATEGORY_ID)
    if category:
        for channel in category.text_channels:
            if channel.id != SUBMIT_TASK_CHANNEL_ID:
                await channel.delete(reason="Cleaning up on bot restart")

    message_content = (
        "Greetings Applicant,\n\n"
        "Should you need to submit a task, kindly click the '**Submit Task**' button below.\n "
        "A private channel will be allocated for your submission. Rest assured, you won't be alone;\n "
        "I'll be there to assist you throughout your submission process."
    )
    view = SubmitView()
    await submit_channel.send(message_content, view=view)



 


@bot.event
async def handle_delayed_reply(message):
    await asyncio.sleep(30)
    history = [msg async for msg in message.channel.history(limit=10) if msg.id > message.id]
    if not history:
        response = random.choice(RESPONSES)
        await message.reply(response, mention_author=True)


#Auto Role
REACTION_MESSAGE_ID = 1232692142770749462  

roles_info = {
    "📚": "Content Department",
    "🎤": "Event Moderation Department",
    "👨‍🏫": "ETA Department",  
    "🖥️": "Graph/IT Department"  
}

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id == REACTION_MESSAGE_ID:
        guild = bot.get_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        if member and not member.bot:
            emoji = str(payload.emoji)
            role_name = roles_info.get(emoji)
            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await member.add_roles(role)
                    print(f"Added {role_name} to {member.name}")
                else:
                    print(f"Role '{role_name}' not found in the server.")
            else:
                print(f"Emoji {emoji} is not configured for any role.")
        else:
            print(f"Member not found or is a bot for user_id {payload.user_id}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id == REACTION_MESSAGE_ID:
        guild = bot.get_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        if member and not member.bot:
            emoji = str(payload.emoji)
            role_name = roles_info.get(emoji)
            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await member.remove_roles(role)
                    print(f"Removed {role_name} from {member.name}")
                else:
                    print(f"Role '{role_name}' for removal not found in the server.")
            else:
                print(f"Emoji {emoji} configured role is not available for removal.")
        else:
            print(f"Member not found or is a bot for user_id {payload.user_id}")



# UNIQUE TASK IDs
async def generate_unique_id(bot, id_storage_channel_id, department):
    prefix_mapping = {
        "ETA Department": "Et",
        "Content Department": "C",
        "Event Moderation Department": "Em",
        "Graph/IT Department": "Gi"
    }
    prefix = prefix_mapping.get(department, "")  # Get the prefix or default to empty string if not found
    alphabet = string.ascii_letters + string.digits  # Includes A-Z, a-z, 0-9

    id_storage_channel = bot.get_channel(id_storage_channel_id)

    # Retrieve existing IDs from the channel
    existing_ids = set()
    async for message in id_storage_channel.history(limit=None):  # Fetch all messages
        existing_ids.add(message.content.split('\n')[0])  # Assuming the first line is the task ID

    # Generate a unique ID with the department prefix
    while True:
        task_id = prefix + ''.join(secrets.choice(alphabet) for _ in range(5))
        if task_id not in existing_ids:
            return task_id


# Utility to find role by name, case-insensitively
def find_role_by_name(guild, role_name):
    return discord.utils.find(lambda r: r.name.lower() == role_name.lower(), guild.roles)

# Utility to send detailed error messages
async def send_error_message(ctx, error_message):
    await ctx.send(f"Error: {error_message}", delete_after=10)  # Deletes after 10 seconds

#ASSIGN
@bot.command()
async def assign(ctx, role_name: str, *, task):
    """Assigns a task to a role and announces it in a specific channel with a role mention and a unique task ID."""
    role = find_role_by_name(ctx.guild, role_name)
    channel_mapping = {
        "Content Department": "content-tasks",
        "ETA Department": "eta-tasks",
        "Event Moderation Department": "emod-tasks",
        "Graph/IT Department": "graphit-tasks"
    }
    submit_channel_mapping = {
        "Content Department": "content-submit",
        "ETA Department": "eta-submit",
        "Event Moderation Department": "emod-submit",
        "Graph/IT Department": "graphit-submit"
    }

    if not role:
        return await send_error_message(ctx, "Role not found. Please check the role name and try again.")

    task_channel = discord.utils.get(ctx.guild.text_channels, name=channel_mapping.get(role_name))
    submit_channel = discord.utils.get(ctx.guild.text_channels, name=submit_channel_mapping.get(role_name))
    if not task_channel or not submit_channel:
        return await send_error_message(ctx, "Assigned channel or submit channel not found. Please check the configuration.")

    id_storage_channel_id = 1235662235976728576
    task_id = await generate_unique_id(bot, id_storage_channel_id, role_name)

    # Send message to the task channel
    task_message = f"{role.mention} New task assigned to {role_name}: {task} [Task ID: {task_id}] ❗"
    await task_channel.send(task_message)

    # Send initial submission prompt to the submit channel and create a thread
    submit_message = await submit_channel.send(f"[TASK ID: {task_id}] Any Submission to the task: {task} will be available in this message thread.")
    submission_thread = await submit_message.create_thread(name=f"Task {task_id} Submissions")
    
    # Send a new message inside the thread
    await submission_thread.send("New messages will be available here.")

    # Send the task ID with thread location after creating the thread
    await bot.get_channel(id_storage_channel_id).send(f"{task_id}\nSubmission Thread location: {submission_thread.id}")

    await ctx.send(f"Task assigned to {role.name} and announced in {task_channel.name} with Task ID: {task_id}. Submissions can be made in the thread in {submit_channel.name}.")



#TASK LIST
@bot.command()
async def task_list(ctx):
    """Lists all pending tasks for all departments, formatted neatly."""
    channel_mapping = {
        "Content Department": "content-tasks",
        "ETA Department": "eta-tasks",
        "Event Moderation Department": "emod-tasks",
        "Graph/IT Department": "graphit-tasks"
    }

    response = []
    index = 1  # To number each department
    for role_name, channel_name in channel_mapping.items():
        channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
        tasks = []
        if channel:
            # Fetch a limited number of messages from the channel's history
            async for message in channel.history(limit=100):  # Adjust limit as necessary
                if "❗" in message.content:  # Assuming '❗' indicates a pending task
                    # Skip the repetitive part of the message to extract just the task
                    task_start_index = message.content.find(":") + 2  # Adjust based on your message format
                    task_description = message.content[task_start_index:]
                    tasks.append(task_description)
        
        if tasks:
            formatted_tasks = "\n".join(f"   {chr(97 + idx)}. {task}" for idx, task in enumerate(tasks))
            response.append(f"{index}. {role_name}:\n{formatted_tasks}")
            index += 1

    if response:
        await ctx.send("\n\n".join(response))
    else:
        await ctx.send("No pending tasks found.")



#SUBMIT
SUBMIT_TASK_CHANNEL_ID = 1233454738285264927  
SUBMIT_CATEGORY_ID = 1233454642550280312 

class SubmitView(discord.ui.View):
    @discord.ui.button(label="Submit Task", style=discord.ButtonStyle.green, custom_id="submit_task_button")
    async def submit_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("This feature is not available in DMs.", ephemeral=True)
            return

        category = interaction.guild.get_channel(SUBMIT_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("Error: Submission category not found. Please contact an administrator.", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            bot.user: discord.PermissionOverwrite(read_messages=True)
        }

        channel_name = f"submission-{interaction.user.display_name.lower().replace(' ', '-')}"
        private_channel = await interaction.guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        await send_greeting(private_channel, interaction.user)
        view = DepartmentSelect(interaction.user, private_channel)
        await private_channel.send("Please select the department for which you are making a submission:", view=view)

        # Continue with the auto-delete setup
        await asyncio.sleep(600)  # Sleep for 600 seconds (10 minutes)
        await private_channel.delete(reason="Auto-delete after 10 minutes")



async def send_greeting(channel, user):
    greetings = [
        f"Ooof, I was exactly waiting for your submission, {user.mention}! Remember, you have 10 minutes to complete this task before this channel disappears.",
        f"DANGER! {user.mention}, proceed only if you're ready to submit. This channel will self-destruct in 10 minutes.",
        f"Ah, {user.mention}! The stage is set, the lights are on, and you've got 10 minutes to shine before this channel closes.",
        f"Welcome, {user.mention}! Don't mind the mess; I'm just making room for your awesome submission. Just so you know, this channel will vanish in 10 minutes.",
        f"Look who's here! {user.mention}, ready to drop another masterpiece? Make it quick, though; this channel is on a 10-minute timer!",
        f"Hello {user.mention}, your private podium awaits! You have 10 minutes to deliver your brilliance before the curtains close.",
        f"Hey {user.mention}, ready to rock the stage? You've got 10 minutes to wow us, starting now!",
        f"Enter the spotlight, {user.mention}! You have a brief window of 10 minutes to leave your mark.",
        f"Ready, set, go {user.mention}! Your mission, should you choose to accept it, lasts only 10 minutes. Make them count!",
        f"Tick-tock, {user.mention}! The countdown of 10 minutes begins now. Let’s see what you've got!"
    ]
    greeting = random.choice(greetings)
    await channel.send(greeting)

class DepartmentSelect(discord.ui.View):
    def __init__(self, user, channel):
        super().__init__()
        self.user = user
        self.channel = channel  # Store the channel where this view is used

    @discord.ui.select(
        placeholder="Choose your department",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Content Department", description="Submit your content tasks", value="Content"),
            discord.SelectOption(label="Event Moderation Department", description="Submit your event moderation tasks", value="Event Moderation"),
            discord.SelectOption(label="ETA Department", description="Submit your ETA tasks", value="ETA"),
            discord.SelectOption(label="Graph/IT Department", description="Submit your Graph/IT tasks", value="Graph/IT"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.user_selection = select.values[0]
        await interaction.response.send_message(f"You have selected the {self.user_selection} department.", ephemeral=True)
        prompt_message = await self.channel.send(f"{interaction.user.mention}, please type down the task ID for your submission in the {self.user_selection} department.")
        # Set the state as awaiting a task ID
        awaiting_task_id[self.channel.id] = self.user_selection
        self.stop()


awaiting_task_id = {}

@bot.event
async def on_message(message):
    if message.author.bot or not message.content:
        return

    # Check if this channel is expecting a task ID
    if message.channel.id in awaiting_task_id:
        department = awaiting_task_id[message.channel.id]
        task_id = message.content.strip()
        task_channel_name = f"{department.lower()}-tasks"
        task_channel = discord.utils.get(message.guild.text_channels, name=task_channel_name)

        # Verify task ID
        task_description = None
        async for msg in task_channel.history(limit=200):  # Limit might be adjusted based on actual usage
            if f"[Task ID: {task_id}]" in msg.content:
                start = msg.content.find(':') + 2
                end = msg.content.find(' [')
                task_description = msg.content[start:end]
                break

        if task_description:
            await message.channel.send(f"Your Task ID is verified!\nYou are submitting for the task: {task_description}")
            # Clear the state indicating awaiting task ID
            del awaiting_task_id[message.channel.id]
        else:
            await message.channel.send("Task ID not found. Please enter a valid task ID.")

    # Regular message handling
    await bot.process_commands(message)

        



bot.run(TOKEN)