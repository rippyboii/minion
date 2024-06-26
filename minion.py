#Author -> Apeel Subedi

import discord
import asyncio
from discord.ext import commands
import random
from dotenv import load_dotenv
import os
import secrets
import string
from discord.ui import Button, View
from discord import ButtonStyle

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True
intents.members = True

data_lock = asyncio.Lock()

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=intents)

GREETINGS = ["hi", "hello", "namaste"]
RESPONSES = [
    "Seems like you have no one to play with, so Namaste there!",
    "Namaste? Anyone there? Well, I'm here for you!",
    "Looks like it's just you and me here, Namaste!",
    "Echo... Echo... Just kidding, I'm here.",
    "Lonely? Don't worry, you've got company!"
]

# Channel mappings for tasks and submission
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

department_selection = {}  # Dictionary to store selected department by channel ID
task_details = {}  # Dictionary to store task details by channel ID

LOGGING_CHANNEL_ID = 1241590035464192080  # Channel ID for logging

async def log_to_channel(bot, message):
    """Sends a log message to the specified logging channel."""
    channel = bot.get_channel(LOGGING_CHANNEL_ID)
    if channel:
        await channel.send(message)

async def keep_alive():
    while True:
        await asyncio.sleep(300)  # Sleep for 5 minutes
        try:
            print("Keep-alive check")
        except Exception as e:
            print(f"Error in keep-alive check: {e}")

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    bot.loop.create_task(keep_alive())  # Start keep-alive task

    try:
        category = bot.get_channel(SUBMIT_CATEGORY_ID)
        if category:
            for channel in category.channels:
                if channel.id != SUBMIT_TASK_CHANNEL_ID:
                    await channel.delete()
                    print(f"Deleted channel {channel.name}")
        submit_channel = bot.get_channel(SUBMIT_TASK_CHANNEL_ID)
        if submit_channel:
            await submit_channel.purge(limit=None)
            message_content = (
                "Greetings, Applicant!\n\n"
                "Welcome to the dedicated task submission channel. If you have work to submit, you're in the right place! "
                "Simply click the 'Submit Task' button below to begin. A quiet, dedicated channel will be created specifically for your submission. "
                "Don't worry—I'll be there to guide you every step of the way."
            )
            view = View(timeout=None)  # Disable timeout
            submit_button = SubmitTaskButton()
            view.add_item(submit_button)
            await submit_channel.send(message_content, view=view)
            await log_to_channel(bot, "Bot is ready and submission channel is set up.")
        else:
            print("Error: Submit channel not found.")
    except Exception as e:
        print(f"Error in on_ready: {e}")
        await log_to_channel(bot, f"Error in on_ready: {e}")

@bot.event
async def handle_delayed_reply(message):
    await asyncio.sleep(30)
    history = [msg async for msg in message.channel.history(limit=10) if msg.id > message.id]
    if not history:
        response = random.choice(RESPONSES)
        await message.reply(response, mention_author=True)

# Auto Role
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
                    await log_to_channel(bot, f"Added {role_name} to {member.name}")
                else:
                    print(f"Role '{role_name}' not found in the server.")
                    await log_to_channel(bot, f"Role '{role_name}' not found in the server.")
            else:
                print(f"Emoji {emoji} is not configured for any role.")
                await log_to_channel(bot, f"Emoji {emoji} is not configured for any role.")
        else:
            await log_to_channel(f"Member not found or is a bot for user_id {payload.user_id}")

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
                    await log_to_channel(bot, f"Removed {role_name} from {member.name}")
                else:
                    print(f"Role '{role_name}' for removal not found in the server.")
                    await log_to_channel(bot, f"Role '{role_name}' for removal not found in the server.")
            else:
                print(f"Emoji {emoji} configured role is not available for removal.")
                await log_to_channel(bot, f"Emoji {emoji} configured role is not available for removal.")
        else:
            await log_to_channel(f"Member not found or is a bot for user_id {payload.user_id}")

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
    await log_to_channel(bot, f"Error: {error_message}")

# ASSIGN
@bot.command()
async def assign(ctx, role_name: str, *, task):
    """Assigns a task to a role and announces it in a specific channel with a role mention and a unique task ID."""
    role = find_role_by_name(ctx.guild, role_name)
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
    await log_to_channel(bot, f"{ctx.author} assigned task to {role_name} with Task ID: {task_id}")

    # Send initial submission prompt to the submit channel and create a thread
    submit_message = await submit_channel.send(f"[TASK ID: {task_id}] Any Submission to the task: {task} will be available in this message thread.")
    submission_thread = await submit_message.create_thread(name=f"Task {task_id} Submissions")
    
    # Send a new message inside the thread
    await submission_thread.send("New messages will be available here.")
    await log_to_channel(bot, f"Created submission thread for Task ID: {task_id}")

    # Send the task ID with thread location after creating the thread
    await bot.get_channel(id_storage_channel_id).send(f"{task_id}\nSubmission Thread location: {submission_thread.id}")

    await ctx.send(f"Task assigned to {role.name} and announced in {task_channel.name} with Task ID: {task_id}. Submissions can be made in the thread in {submit_channel.name}.")


# TASK LIST
@bot.command()
async def task_list(ctx):
    """Lists all pending tasks for all departments, formatted neatly."""
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

class SupportButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label="Support 🎗️", custom_id="support_request")

    async def callback(self, interaction: discord.Interaction):
        support_category_id = 1239619528539902013
        support_category = interaction.guild.get_channel(support_category_id)
        try:
            if support_category:
                await interaction.channel.edit(category=support_category)
                support_role = interaction.guild.get_role(1232694582114783232)
                if support_role:
                    await interaction.channel.send(f"This channel is now under support, {support_role.mention} will take care of your problem.")
                    await log_to_channel(bot, f"{interaction.user.name} requested support during their taks submission.")
                else:
                    await interaction.channel.send("Support role not found.")
            else:
                await interaction.channel.send("Support category not found.")
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}")
            print(f"Error in SupportButton callback: {e}")
            await log_to_channel(bot, f"Error in SupportButton callback: {e}")

        # Correctly stopping the view associated with the message
        if interaction.message:
            for component in interaction.message.components:
                for item in component.children:
                    if isinstance(item, View):
                        item.stop()

class SubmitTaskButton(Button):
    def __init__(self):
        super().__init__(label="Submit Task", style=ButtonStyle.green, custom_id="submit_task")

    async def callback(self, interaction: discord.Interaction):
        category = bot.get_channel(SUBMIT_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("Submission category not found.", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }
        
        try:
            channel = await interaction.guild.create_text_channel("submission", category=category, overwrites=overwrites)
            await self.send_greeting(channel, interaction.user)

            view = DepartmentView(timeout=None)  # Disable timeout
            await channel.send("Please select the department for which this task is intended:", view=view)
            await log_to_channel(bot, f"Created submission channel for {interaction.user.name}")

            # Optionally delete the channel or handle cleanup
            await asyncio.sleep(600)  # Example: wait 10 minutes before cleanup
            await channel.delete()
            await log_to_channel(bot, f"Deleted submission channel for {interaction.user.name} after 10 minutes.")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            print(f"Error in SubmitTaskButton callback: {e}")
            await log_to_channel(bot, f"Error in SubmitTaskButton callback: {e}")

    @staticmethod
    async def send_greeting(channel, user):
        greetings = [
            f"Ooof, I was exactly waiting for your submission, {user.mention}! 😄 Remember, you have 10 minutes to complete this task before this channel disappears. ⏳",
            f"DANGER! {user.mention}, proceed only if you're ready to submit. This channel will self-destruct in 10 minutes. 💥",
            f"Ah, {user.mention}! The stage is set, the lights are on, and you've got 10 minutes to shine before this channel closes. 🌟",
            f"Welcome, {user.mention}! Don't mind the mess; I'm just making room for your awesome submission. Just so you know, this channel will vanish in 10 minutes. 🚀",
            f"Look who's here! {user.mention}, ready to drop another masterpiece? Make it quick, though; this channel is on a 10-minute timer! 🎨",
            f"Hello {user.mention}, your private podium awaits! You have 10 minutes to deliver your brilliance before the curtains close. 🎭",
            f"Hey {user.mention}, ready to rock the stage? You've got 10 minutes to wow us, starting now! 🎸",
            f"Enter the spotlight, {user.mention}! You have a brief window of 10 minutes to leave your mark. 🌟",
            f"Ready, set, go {user.mention}! Your mission, should you choose to accept it, lasts only 10 minutes. Make them count! ⌛",
            f"Tick-tock, {user.mention}! The countdown of 10 minutes begins now. Let’s see what you've got! ⏰"
        ]
        greeting = random.choice(greetings)
        await channel.send(greeting)

        support_button = SupportButton()  # Create the support button
        support_view = View(timeout=None)  # Disable timeout
        support_view.add_item(support_button)
        await channel.send("If you need support, click the button below:", view=support_view)

class DepartmentSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Content Department", description="Submit tasks for content creation."),
            discord.SelectOption(label="ETA Department", description="Submit tasks for educational and training activities."),
            discord.SelectOption(label="Event Moderation Department", description="Submit tasks related to event management and moderation."),
            discord.SelectOption(label="Graph/IT Department", description="Submit tasks for IT and graphic design.")
        ]

        super().__init__(placeholder="Choose the department for your task...",
                         min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            self.view.department = self.values[0]
            department_selection[interaction.channel_id] = self.values[0]
            await interaction.response.send_message(f"You have selected the {self.values[0]}. Please enter the task ID for which you are submitting the work: \n \n  💡 **Tip:** You can find the task id in the respective department's task channel 💡 ", ephemeral=True)
            
            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user

            msg = await bot.wait_for('message', check=check, timeout=600)
            task_id = msg.content.strip()

            # Retrieve the selected department from the stored data
            department = department_selection.get(interaction.channel_id)

            # Search for the task ID in the respective department's task channel
            task_channel_name = channel_mapping.get(department)
            task_channel = discord.utils.get(interaction.guild.text_channels, name=task_channel_name)
            task_description = None

            if task_channel:
                async for message in task_channel.history(limit=100):  # Adjust limit as necessary
                    if f"[Task ID: {task_id}]" in message.content:
                        task_description_start = message.content.find(":") + 2
                        task_description_end = message.content.find("[Task ID:") - 1
                        task_description = message.content[task_description_start:task_description_end].strip()
                        break

                if task_description:
                    task_details[interaction.channel_id] = {
                        "task_id": task_id,
                        "task_description": task_description,
                        "department": department
                    }
                    await interaction.channel.send(f"Task ID: {task_id}\nTask Description: {task_description}\n\nPlease submit your work.\n\n💡 **Tip:** If you are trying to upload a file as your submission, please note that I cannot process the file directly. Instead, provide a link to the file on a drive with public access enabled, and I can update your submission accordingly. 💡")
                    await self.wait_for_submission(interaction)
                else:
                    await interaction.channel.send(f"Task ID {task_id} not found in the {department} tasks.")
            else:
                await interaction.channel.send(f"Task channel for {department} not found.")

        except asyncio.TimeoutError:
            await interaction.channel.send("You did not provide a task ID in time. Please try again.")
            await interaction.channel.delete()
            await log_to_channel(bot, f"Task ID not provided in time for user {interaction.user.display_name}. Channel deleted.")

    async def wait_for_submission(self, interaction):
        def check(m):
            return m.channel == interaction.channel and m.author == interaction.user

        try:
            submission_msg = await bot.wait_for('message', check=check, timeout=600)
            task_details[interaction.channel_id]["submission"] = submission_msg.content

            comment_view = CommentView(timeout=None)  # Disable timeout
            await interaction.channel.send("Would you like to add a comment to your submission? \n \n 💡 **Did you know?** MIN reserves the right to use your submitted content without notifying you or giving credit. If you prefer your content to be evaluated only and not used otherwise, please mention this in your comment. 💡", view=comment_view)
            await log_to_channel(bot, f"Received submission task ID: {task_details[interaction.channel_id]['task_id']}")
        except asyncio.TimeoutError:
            await interaction.channel.send("You did not submit your work in time. Please try again.")
            await interaction.channel.delete()
            await log_to_channel(bot, f"Submission not provided in time. Channel deleted for user {interaction.user}.")

class CommentView(discord.ui.View):
    def __init__(self, timeout=None):  # Disable timeout
        super().__init__(timeout=timeout)
        self.add_item(AddCommentButton())
        self.add_item(NoCommentButton())

class AddCommentButton(Button):
    def __init__(self):
        super().__init__(label="Add Comment", style=ButtonStyle.blurple, custom_id="add_comment")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please enter your comment: ", ephemeral=True)
        def check(m):
            return m.channel == interaction.channel and m.author == interaction.user

        try:
            comment_msg = await bot.wait_for('message', check=check, timeout=600)
            task_details[interaction.channel_id]["comment"] = comment_msg.content
            await interaction.channel.send("Thank you! \n I have noted your comment!")
            await generate_report(interaction)
        except asyncio.TimeoutError:
            await interaction.channel.send("You did not provide a comment in time. Please try again.")
            await interaction.channel.delete()
            await log_to_channel(bot, "Comment not provided in time. Channel deleted.")

class NoCommentButton(Button):
    def __init__(self):
        super().__init__(label="No Comment", style=ButtonStyle.grey, custom_id="no_comment")

    async def callback(self, interaction: discord.Interaction):
        task_details[interaction.channel_id]["comment"] = "No Comment"
        await generate_report(interaction)

async def generate_report(interaction):
    channel_id = interaction.channel_id
    details = task_details[channel_id]

    report = (
        f"**TASK SUBMISSION FOR {interaction.user.display_name}**\n\n"
        f"**Department:** {details['department']}\n"
        f"**Task Name:** {details['task_description']}\n"
        f"**Task ID:** {details['task_id']}\n\n"
        f"**Comment:** {details.get('comment', 'No Comment')}\n\n"
        f"**Task:** {details['submission']}"
    )

    view = ReportConfirmationView(timeout=None)  # Disable timeout
    await interaction.channel.send(report, view=view)

class ReportConfirmationView(discord.ui.View):
    def __init__(self, timeout=None):  # Disable timeout
        super().__init__(timeout=timeout)
        self.add_item(CorrectButton())
        self.add_item(IncorrectButton())

class CorrectButton(Button):
    def __init__(self):
        super().__init__(label="Correct", style=ButtonStyle.green, custom_id="correct")

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        details = task_details[channel_id]

        task_id = details['task_id']
        id_storage_channel = bot.get_channel(1235662235976728576)  # ID of the channel where task-ids are stored

        submission_thread_location = None

        # Debug message: Start of task ID search
        await interaction.channel.send(f"Searching for task ID: {task_id} in the task-ids channel.")

        # Improved search logic
        async for message in id_storage_channel.history(limit=None):
            lines = message.content.split('\n')
            if lines[0] == task_id:
                submission_thread_location = lines[1].replace("Submission Thread location: ", "")
                break

        # Debug message: Task ID search result
        if submission_thread_location:
            await interaction.channel.send(f"Found submission thread location: {submission_thread_location}.")
        else:
            await interaction.channel.send("Task ID not found in task-ids channel. Please contact support.")
            await log_to_channel(bot, f"Task ID {task_id} not found in task-ids channel.")
            return

        # Debug message: Retrieving the submission thread
        await interaction.channel.send(f"Retrieving submission thread: {submission_thread_location}.")

        try:
            submission_thread = await interaction.guild.fetch_channel(int(submission_thread_location))
            if submission_thread:
                report = (
                    f"**TASK SUBMISSION FOR {interaction.user.display_name}**\n\n"
                    f"**Department:** {details['department']}\n"
                    f"**Task Name:** {details['task_description']}\n"
                    f"**Task ID:** {details['task_id']}\n\n"
                    f"**Comment:** {details.get('comment', 'No Comment')}\n\n"
                    f"**Task:** {details['submission']}"
                )
                approve_view = View(timeout=None)  # Disable timeout
                approve_view.add_item(ApproveButton())  # Add ApproveButton to the view
                await submission_thread.send(report, view=approve_view)
                await interaction.channel.send("Your submission is complete! 🎉")
                await log_to_channel(bot, f"Submission complete for task ID: {task_id} by applicant {interaction.user.display_name}")
            else:
                await interaction.channel.send("Submission thread not found. Please contact support.")
                await log_to_channel(bot, "Submission thread not found.")
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}")
            await log_to_channel(bot, f"Error retrieving submission thread: {e}")

class IncorrectButton(Button):
    def __init__(self):
        super().__init__(label="Incorrect", style=ButtonStyle.red, custom_id="incorrect")

    async def callback(self, interaction: discord.Interaction):
        await interaction.channel.send("You need to restart your submission as this one is discarded. This channel will be deleted in a minute.")
        await asyncio.sleep(60)
        await interaction.channel.delete()

class DepartmentView(discord.ui.View):
    def __init__(self, timeout=None):  # Disable timeout
        super().__init__(timeout=timeout)
        self.add_item(DepartmentSelect())
        self.department = None  # Initialize with no department selected

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Optional: Implement custom logic to check the interaction
        return True
    

#APPROVE
class ApproveButton(Button):
    def __init__(self):
        super().__init__(label="Approve ✅", style=ButtonStyle.green, custom_id="approve")

    async def callback(self, interaction: discord.Interaction):
        # Ensure only users with specific roles can approve
        allowed_roles = {1232694582114783232, 1239882455067000955}
        user_roles = {role.id for role in interaction.user.roles}

        if not allowed_roles.intersection(user_roles):
            await interaction.response.send_message("You do not have permission to approve tasks.", ephemeral=True)
            return

        # Retrieve the task details from the message
        message_content = interaction.message.content.split('\n')

        # Debug logging
        print(f"Message content: {message_content}")
        print(f"Message content length: {len(message_content)}")

        # Print each line for debugging
        for i, line in enumerate(message_content):
            print(f"Line {i}: {line}")

        try:
            # Check if the length of the message content is at least 9
            if len(message_content) < 9:
                raise IndexError("Message content is not of expected length.")

            # Extract the relevant fields
            department_line = message_content[2].strip()
            task_description_line = message_content[3].strip()
            task_id_line = message_content[4].strip()
            task_content_line = message_content[8].strip()

            # Debug each part
            await log_to_channel(bot, f"Trying to parse department: {department_line}")
            if not department_line.startswith("**Department:**"):
                raise ValueError(f"Unexpected format for department line: {department_line}")
            department = department_line.split("**Department:** ", 1)[1].strip()

            await log_to_channel(bot, f"Trying to parse task description: {task_description_line}")
            if not task_description_line.startswith("**Task Name:**"):
                raise ValueError(f"Unexpected format for task description line: {task_description_line}")
            task_description = task_description_line.split("**Task Name:** ", 1)[1].strip()

            await log_to_channel(bot, f"Trying to parse task ID: {task_id_line}")
            if not task_id_line.startswith("**Task ID:**"):
                await log_to_channel(bot, f"Problematic Task ID Line: {task_id_line}")
                raise ValueError(f"Unexpected format for task ID line: {task_id_line}")
            task_id = task_id_line.split("**Task ID:** ", 1)[1].strip()

            await log_to_channel(bot, f"Trying to parse task content: {task_content_line}")
            if not task_content_line.startswith("**Task:**"):
                raise ValueError(f"Unexpected format for task content line: {task_content_line}")
            task_content = task_content_line.split("**Task:** ", 1)[1].strip()

            # Debug each parsed value
            await log_to_channel(bot, f"Department: {department}")
            await log_to_channel(bot, f"Task Description: {task_description}")
            await log_to_channel(bot, f"Task ID: {task_id}")
            await log_to_channel(bot, f"Task Content: {task_content}")

        except (IndexError, ValueError) as e:
            print(f"Error parsing message content: {e}")
            await interaction.response.send_message("Failed to parse the message content. Please contact support.", ephemeral=True)
            await log_to_channel(bot, f"Error parsing message content: {e}")
            return
        except Exception as e:
            print(f"Unexpected error: {e}")
            await interaction.response.send_message("An unexpected error occurred. Please contact support.", ephemeral=True)
            await log_to_channel(bot, f"Unexpected error: {e}")
            return

        department_roles = {
            "Content Department": 1231624847855980635,
            "Graph/IT Department": 1231625024461344840,
            "ETA Department": 1231624980547113052,
            "Event Moderation Department": 1231624922393088081
        }

        department_role_id = department_roles.get(department, None)

        if not department_role_id:
            await interaction.response.send_message("Department role not found. Please contact support.", ephemeral=True)
            return

        approved_channel = bot.get_channel(1233852997797417030)
        if not approved_channel:
            await interaction.response.send_message("Approved task showcase channel not found. Please contact support.", ephemeral=True)
            await log_to_channel(bot, "Approved task showcase channel not found.")
            return

        # Send the approval message to the approved task showcase channel
        approved_message = await approved_channel.send(
            f"<@&{department_role_id}>, an executive has approved a task!\n\n"
            f"**Task Description:** {task_description}\n\n"
            f"**Approved by:** {interaction.user.display_name}"
        )

        # Create a thread in the approved message and post the task for discussion
        discussion_thread = await approved_message.create_thread(name=f"Task {task_id} Discussion")
        await discussion_thread.send(
            f"**Task:** {task_content}\n\n"
            f"Feel free to discuss the approved task here."
        )

        await interaction.response.send_message("The task has been approved and posted in the approved task showcase channel.", ephemeral=True)
        await log_to_channel(bot, f"Task ID: {task_id} approved by {interaction.user.display_name} and posted in the approved task showcase channel.")



#temporary approval
@bot.command()
async def approve(ctx, message_id: int):
    """Approves a task based on the message ID, can only be used by executives or bot helpers."""
    # Check if the command is run in a thread
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be run within a thread.")
        return

    # Check if the user has the required roles
    allowed_roles = {1239882455067000955, 1232694582114783232}
    user_roles = {role.id for role in ctx.author.roles}

    if not allowed_roles.intersection(user_roles):
        await ctx.send("You do not have permission to approve tasks.")
        return

    # Find the message in the thread
    try:
        message = await ctx.channel.fetch_message(message_id)
    except discord.NotFound:
        await ctx.send("Message not found.")
        return

    # Extract task description from the message
    task_description = message.content

    # Define department roles mapping
    temp_department_roles = {
        "Content Department": 1231624847855980635,
        "Graph/IT Department": 1231625024461344840,
        "ETA Department": 1231624980547113052,
        "Event Moderation Department": 1231624922393088081
    }

    # Determine the department based on the category of the thread
    category_name = ctx.channel.category.name if ctx.channel.category else None
    department_role_id = temp_department_roles.get(category_name)

    if not department_role_id:
        await ctx.send("Department role not found. Please contact support.")
        return

    # Get the approved task showcase channel
    approved_channel = bot.get_channel(1233852997797417030)
    if not approved_channel:
        await ctx.send("Approved task showcase channel not found. Please contact support.")
        return

    # Send the approval message to the approved task showcase channel
    approved_message = await approved_channel.send(
        f"<@&{department_role_id}>, an executive has approved a task!\n\n"
        f"**Task Description:** Check the thread for discussion and approved task description\n\n"
        f"**Approved by:** {ctx.author.display_name}"
    )

    # Create a thread in the approved message and post the task for discussion
    discussion_thread = await approved_message.create_thread(name=f"Task Discussion")
    await discussion_thread.send(
        f"**Task:** {task_description}\n\n"
        f"Feel free to discuss the approved task here."
    )

    await ctx.send("The task has been approved and posted in the approved task showcase channel.")
    await log_to_channel(bot, f"Task approved by {ctx.author.display_name} and posted in the approved task showcase channel.")


# CLEAR TASK
@bot.command()
async def clear_task(ctx, task_id: str):
    """Clears a task based on the task ID, can only be used by executives or bot helpers."""
    allowed_roles = {1232694582114783232, 1239882455067000955}
    user_roles = {role.id for role in ctx.author.roles}

    if not allowed_roles.intersection(user_roles):
        await ctx.send("You do not have permission to clear tasks.")
        return

    # Determine the department from the task ID prefix
    department_prefix_mapping = {
        "C": "Content Department",
        "Et": "ETA Department",
        "Em": "Event Moderation Department",
        "Gi": "Graph/IT Department"
    }

    prefix = next((k for k in department_prefix_mapping if task_id.startswith(k)), None)
    if not prefix:
        await ctx.send("Invalid task ID prefix.")
        return

    department = department_prefix_mapping[prefix]
    task_channel_name = channel_mapping.get(department)
    id_storage_channel_id = 1235662235976728576

    # Find and delete the task message in the department task channel
    task_channel = discord.utils.get(ctx.guild.text_channels, name=task_channel_name)
    if not task_channel:
        await ctx.send(f"Task channel for {department} not found.")
        return

    task_message_found = False
    async for message in task_channel.history(limit=100):  # Adjust limit as necessary
        if f"[Task ID: {task_id}]" in message.content:
            await message.delete()
            task_message_found = True
            break

    if not task_message_found:
        await ctx.send(f"Task ID {task_id} not found in the {department} tasks.")
        return

    # Find and delete the task ID message in the task-ids channel
    id_storage_channel = bot.get_channel(id_storage_channel_id)
    if not id_storage_channel:
        await ctx.send("Task-ids channel not found.")
        return

    task_id_message_found = False
    async for message in id_storage_channel.history(limit=None):
        if message.content.startswith(task_id):
            await message.delete()
            task_id_message_found = True
            break

    if task_id_message_found:
        await ctx.send(f"Task ID {task_id} has been cleared.")
    else:
        await ctx.send(f"Task ID {task_id} was not found in the task-ids channel.")


bot.run(os.getenv("TOKEN"))
