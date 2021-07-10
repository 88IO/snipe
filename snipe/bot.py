import discord
import asyncio
import traceback
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from datetime import timedelta, timezone, datetime
from collections import deque
from .config import TOKEN
from .task import Task


EXTENSIONS = [
    "snipe.cogs.schedule",
    "snipe.cogs.slash_schedule",
    "snipe.cogs.voice",
    "snipe.cogs.show",
    "snipe.cogs.cancel"
]

class Bot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.timezone = timezone(timedelta(hours=+9), 'JST')
        self.tasks = {}
        self.vc = {}

        self._slash = SlashCommand(self, sync_commands=True)

        for cog in EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception:
                print("Failed to load extension:", cog)
                traceback.print_exc()

    async def on_command_error(self, _, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.errors.NoPrivateMessage):
            return
        raise error

    async def on_ready(self):
        self.tasks = {guild.id: deque() for guild in self.guilds}
        self.vc = {guild.id:None for guild in self.guilds}

        print("Finish Loading... ready...")
        await self.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing, name="https://github.com/88IO/snipe"))

    async def on_guild_join(self, guild):
        self.tasks[guild.id] = deque()
        self.vc[guild.id] = None

    @tasks.loop(seconds=3)
    async def execute(self):
        print(self.tasks)

        async def run_executable(guild_tasks):
            now = datetime.now(self.timezone)

            executable_tasks = (guild_tasks.popleft() for _ in range(len(guild_tasks))
                                if guild_tasks[0].datetime <= now)

            for task in executable_tasks:
                for member in task.members:
                    if member.voice:
                        if task.type == Task.DISCONNECT:
                            print("DISCONNECT: " + member.display_name)
                            try:
                                await member.send(f"{task.datetime.strftime('%m-%d %H:%M:%S')}に通話を強制切断しました")
                            except discord.errors.HTTPException:
                                pass
                            await member.move_to(None)
                        elif task.type == Task.BEFORE_3MIN:
                            print("BEFORE_3MIN: " + member.display_name)
                            _vc = self.vc[member.guild.id]
                            if _vc and _vc.is_connected() and not _vc.is_playing():
                                _vc.play(discord.FFmpegPCMAudio("snipe/sounds/3min.wav"))
                            try:
                                await member.send("3分後に通話を強制切断します")
                            except discord.errors.HTTPException:
                                pass

        _ = await asyncio.gather(*(run_executable(guild_tasks) for guild_tasks in self.tasks.values()))

        for guild_id, guild_tasks in self.tasks.items():
            if len(guild_tasks):
                return
            else:
                _vc = self.vc[guild_id]
                if _vc and _vc.is_connected():
                    await _vc.disconnect()

        self.execute.stop()


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
