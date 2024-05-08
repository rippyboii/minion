def task_assignment():
        import discord
        from discord.ext import commands
        import asyncio
        import random

        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.reactions = True
        intents.members = True

        client = commands.Bot(command_prefix='!', intents=intents)

        # Tasks now map role IDs to lists of tuples (task, member_id)
        