import discord
from discord.ui import Button, View
from discord.ext import commands

class SubmitButtonView(View):
    @discord.ui.button(label="Submit Task", style=discord.ButtonStyle.green, custom_id="submit_task")
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # Add whatever you want to happen when the button is pressed

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    channel = bot.get_channel(1233454738285264927)  # Use your channel ID here
    view = SubmitButtonView()
    await channel.send("Dear Members,\nReact with this button to submit your completed tasks!", view=view)
    await bot.close()

bot.run('MTIxMTUzMjk4MTc2ODgxNDY3Mg.G21dwX.fprw4dCBsUjwuiE8m7DcPY4krcK60U2A0mg52I')  # Replace 'YOUR_BOT_TOKEN' with your actual token


###How to Run the Script
#Replace 1233454738285264927 with your channel ID.
#Replace 'YOUR_BOT_TOKEN' with your actual Discord bot token.
#Save the script as send_button_message.py.
#Run the script from your terminal: