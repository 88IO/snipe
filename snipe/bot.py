import discord
from discord.ext import commands
import traceback
from .config import TOKEN


EXTENSIONS = [
    "snipe.cogs.cmd"
]

class Bot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix)

        for cog in EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception:
                print("Failed to load extension:", cog)
                traceback.print_exc()

    async def on_ready(self):
        print("ready...")
        await self.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing, name="https://github.com/88IO/snipe"))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error

def main():
    bot = Bot(command_prefix=commands.when_mentioned)
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
