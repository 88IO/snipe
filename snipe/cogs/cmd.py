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

    @tasks.loop(seconds=3)
    async def loop(self):
        print("loop...")
        print(self.tasks)

        while self.tasks and self.tasks[0].datetime <= datetime.datetime.now():
            task = hq.heappop(self.tasks)
            if task.member.voice:
                if task.type == Task.DISCONNECT:
                    await task.member.send(f"{task.datetime}に通話を強制切断しました")
                    await task.member.move_to(None)
                elif task.type == Task.BEFORE_3MIN:
                    await task.member.send("3分後に通話を強制切断します")

    @commands.group()
    async def snipe(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドが必要です")

    @snipe.command()
    async def show(self, ctx):
        embed = discord.Embed(title="通話切断予約", description=f"snipe botによる通話切断予約表です")
        for task in sorted(self.tasks):
            embed.add_field(name=str(task.datetime),
                value=("強制切断" if task.type == Task.DISCONNECT else "3分前連絡") + f": {task.member.display_name}")
        await ctx.send(embed=embed)

    @snipe.command()
    async def connect(self, ctx):
        if ctx.author.voice:
            self.vc = await ctx.author.voice.channel.connect()
            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/connect.wav"), after=lambda _: print("connected"))

    @snipe.command()
    async def disconnect(self, ctx):
        print("call disconnect()")
        if self.vc.is_connected():
            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/disconnect.wav"), after=lambda _: print("disconnected"))
            await self.vc.disconnect()

    @snipe.command()
    async def reserve(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.fullmatch(r"^(?:(?P<hour>\d{1,2})(?:時間|時|:|：|h|H|\s+))?"\
                                 + r"(?:(?P<minute>\d{1,2})(?:分|m|M|))?.*", t):
            hour, minute = map(lambda x: int(x) if x else 0, match.group("hour", "minute"))
            now = datetime.datetime.now()
            disconnect_task = Task(
                now.replace(hour=hour, minute=minute, microsecond=0)
                + datetime.timedelta(
                    days=int(datetime.time(hour=hour, minute=minute) < now.time())),
                ctx.member,
                Task.DISCONNECT)
            hq.heappush(self.tasks, disconnect_task)

            if disconnect_task.datetime - now > datetime.timedelta(minutes=3):
                before3min_task = Task(
                    disconnect_task.datetime - datetime.timedelta(minutes=3),
                    ctx.member,
                    Task.BEFORE_3MIN)
                hq.heappush(self.tasks, before3min_task)

            await ctx.send(f"{disconnect_task.datetime}に"
                           + f"{disconnect_task.member.display_name}を切断します")

    @snipe.command()
    async def reservein(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.fullmatch(r"^(?:(?P<hour>\d{1,2})(?:時間|時|:|：|h|H|\s+))?"\
                                 + r"(?:(?P<minute>\d{1,2})(?:分|m|M|))?.*", t):
            hour, minute = map(lambda x: int(x) if x else 0, match.group("hour", "minute"))
            disconnect_task = Task(
                datetime.datetime.now().replace(microsecond=0)
                  + datetime.timedelta(hours=hour, minutes=minute),
                ctx.member,
                Task.DISCONNECT)
            hq.heappush(self.tasks, disconnect_task)

            if hour * 60 + minute > 3:
                before3min_task = Task(
                    datetime.datetime.now().replace(microsecond=0)
                    + datetime.timedelta(hours=hour, minutes=minute-3),
                    ctx.member,
                    Task.BEFORE_3MIN)
                hq.heappush(self.tasks, before3min_task)

            await ctx.send(f"{disconnect_task.datetime}に"
                           + f"{disconnect_task.member.display_name}を切断します")


def setup(bot):
    bot.add_cog(CmdCog(bot))
