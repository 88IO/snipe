import discord
from discord.ext import commands
import traceback
from .config import TOKEN


EXTENSIONS = [
    "snipe.cogs.cmd"
]

class Bot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)

        for cog in EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception:
                print("Failed to load extension:", cog)
                traceback.print_exc()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.errors.NoPrivateMessage):
            return
        raise error

def main():
    intents = discord.Intents.none()
    intents.guilds = True
    intents.members = True
    intents.voice_states = True
    intents.presences = True
    intents.guild_messages = True
    intents.guild_reactions = True

    bot = Bot(command_prefix=commands.when_mentioned, intents=intents)
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
