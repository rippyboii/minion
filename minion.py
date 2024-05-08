
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

    message_content = (
        "Dear Applicants,\n\n"
        "If you have a task to submit, please press the 'Submit Task' button below. "
        "This will create a private channel for you to submit your task, and don't worry, I will assist you in the process."
    )
 


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




SUBMIT_TASK_CHANNEL_ID = 1233454738285264927  
SUBMIT_CATEGORY_ID = 1233454642550280312 


async def send_greeting(channel, user):
    greetings = [
        f"Ooof, I was exactly waiting for your submission, {user.mention}! Remember, you have 10 minutes to complete this task before this channel disappears.",
        f"DANGER! {user.mention}, proceed only if you're ready to submit. This channel will self-destruct in 10 minutes.",
        f"Ah, {user.mention}! The stage is set, the lights are on, and you've got 10 minutes to shine before this channel closes.",
        f"Welcome, {user.mention}! Don't mind the mess; I'm just making room for your awesome submission. Just so you know, this channel will vanish in 10 minutes.",
        f"Look who's here! {user.mention}, ready to drop another masterpiece? Make it quick, though; this channel is on a 10-minute timer!"
    ]
    greeting = random.choice(greetings)
    await channel.send(greeting)



bot.run(TOKEN)