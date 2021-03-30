from discord.ext import commands, tasks
import discord
import heapq as hq
import datetime
import re
from ..task import Task


class CmdCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = []
        self.vc = None
        self.loop.start()

    @tasks.loop(seconds=10.0)
    async def loop(self):
        print("loop...")
        print(isinstance(self.tasks[0].member if self.tasks else None, discord.Member))
        while self.tasks and self.tasks[0].datetime <= datetime.datetime.now():
            task = hq.heappop(self.tasks)
            if task.member.voice:
                await task.member.send(f"{task.member.display_name}を切断しました")
                await task.member.move_to(None)

    @commands.group()
    async def snipe(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドが必要です")

    @snipe.command()
    async def show(self, ctx):
        for task in sorted(self.tasks):
            await ctx.send(f"{task.datetime}: {task.member.display_name}")

    @snipe.command()
    async def connect(self, ctx):
        if ctx.author.voice:
            self.vc = await ctx.author.voice.channel.connect()
            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/connect.wav"), after=lambda e: print("connected"))

    @snipe.command()
    async def disconnect(self, ctx):
        print("call disconnect()")
        if self.vc.is_connected():
            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/disconnect.wav"), after=lambda e: print("disconnected"))
            await self.vc.disconnect()

    @snipe.command()
    async def reserve(self, ctx, args, member: discord.Member):
        if re.fullmatch("[0-9]{1,2}:[0-9]{1,2}", args):
            d = datetime.datetime.strptime(args, "%M:%S")
            if d < datetime.datetime.now().time():
                new_task = Task(
                    datetime.datetime.now().replace(
                        minutes=d.minute, seconds=d.second, microsecond=0)
                    + datetime.timedelta(hours=1),
                    member if member else ctx.member
                )
            else:
                new_task = Task(
                    datetime.datetime.now().replace(
                        minutes=d.minute, seconds=d.second, microsecond=0),
                    member if member else ctx.member
                )
        elif re.fullmatch("[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}", args):
            d = datetime.datetime.strptime(args, "%H:%M:%S")
            if d < datetime.datetime.now().time():
                new_task = Task(
                    datetime.datetime.now().replace(
                        hours=d.hour, minutes=d.minute, seconds=d.second, microsecond=0)
                    + datetime.timedelta(days=1),
                    member if member else ctx.member
                )
            else:
                new_task = Task(
                    datetime.datetime.now().replace(
                        hours=d.hour, minutes=d.minute, seconds=d.second, microsecond=0),
                    member if member else ctx.member
                )
        else:
            return
        hq.heappush(self.tasks, new_task)
        await ctx.send(f"{new_task.datetime}に{new_task.member.display_name}を切断します")

    @snipe.command()
    async def reservein(self, ctx, args, member: discord.Member):
        if re.fullmatch("[0-9]{1,2}:[0-9]{1,2}", args):
            d = datetime.datetime.strptime(args, "%M:%S")
            new_task = Task(
                datetime.datetime.now().replace(microsecond=0)
                + datetime.timedelta(minutes=d.minute, seconds=d.second),
                member if member else ctx.member
            )
        elif re.fullmatch("[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}", args):
            d = datetime.datetime.strptime(args, "%H:%M:%S")
            new_task = Task(
                datetime.datetime.now().replace(microsecond=0)
                + datetime.timedelta(hours=d.hour, minutes=d.minute, seconds=d.second),
                member if member else ctx.member
            )
        else:
            return
        hq.heappush(self.tasks, new_task)
        await ctx.send(f"{new_task.datetime}に{new_task.member.display_name}を切断します")


def setup(bot):
    bot.add_cog(CmdCog(bot))
