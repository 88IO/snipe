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

    @tasks.loop(seconds=5)
    async def loop(self):
        print(self.tasks)

        while self.tasks and self.tasks[0].datetime <= datetime.datetime.now():
            task = hq.heappop(self.tasks)
            for member in task.members:
                if member.voice:
                    if task.type == Task.DISCONNECT:
                        await member.send(f"{task.datetime}に通話を強制切断しました")
                        await member.move_to(None)
                    elif task.type == Task.BEFORE_3MIN:
                        await member.send("3分後に通話を強制切断します")

    @commands.group()
    async def snipe(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("サブコマンドが必要です")

    @snipe.command()
    async def show(self, ctx):
        embed = discord.Embed(title="射殺予定", description="snipebotの通話切断予定表です")
        for task in sorted(self.tasks):
            embed.add_field(
                name=f"{'強制切断' if task.type == Task.DISCONNECT else '3分前連絡'}: "
                       + task.datetime.strftime("%m-%d %H:%M"),
                value=' '.join(map(lambda m: m.display_name, task.members)))
        await ctx.send(embed=embed)

    @snipe.command()
    async def clear(self, ctx):
        members = set(ctx.message.mentions) | set([ctx.author])

        def remove_members(task):
            task.members -= members
            return task.members

        self.tasks = list(filter(remove_members, self.tasks))
        await ctx.send(f"{', '.join(map(lambda m: m.display_name, members))}を予定から削除しました")

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
        if match := re.match(r"(?:(?P<hour>\d{1,2})(?:時間|時|:|：|h|H|\s^@))?"\
                                 + r"(?:(?P<minute>\d{1,2})(?:分|m|M|))?", t):
            if not any(match.group("hour", "minute")):  return
            now = datetime.datetime.now()
            hour = int(h) if (h := match.group("hour")) else now.hour
            minute = int(m) if (m := match.group("minute")) else now.minute
            disconnect_task = Task(
                now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                + datetime.timedelta(
                    days=int(datetime.time(hour=hour, minute=minute) < now.time())),
                set(ctx.message.mentions) | set([ctx.author]),
                Task.DISCONNECT)
            hq.heappush(self.tasks, disconnect_task)

            if disconnect_task.datetime - now > datetime.timedelta(minutes=3):
                before3min_task = Task(
                    disconnect_task.datetime - datetime.timedelta(minutes=3),
                    disconnect_task.members,
                    Task.BEFORE_3MIN)
                hq.heappush(self.tasks, before3min_task)

            await ctx.send(f"{disconnect_task.datetime}に"
                    + f"{', '.join(map(lambda m: m.display_name, disconnect_task.members))}を切断します")

    @snipe.command()
    async def reservein(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.match(r"(?:(?P<hour>\d{1,2})(?:時間|時|:|：|h|H|\s^@))?"\
                                 + r"(?:(?P<minute>\d{1,2})(?:分|m|M|))?", t):
            if not any(match.group("hour", "minute")):  return
            hour, minute = map(lambda x: int(x) if x else 0, match.group("hour", "minute"))
            disconnect_task = Task(
                datetime.datetime.now().replace(microsecond=0)
                  + datetime.timedelta(hours=hour, minutes=minute),
                set(ctx.message.mentions) | set([ctx.author]),
                Task.DISCONNECT)
            hq.heappush(self.tasks, disconnect_task)

            if hour * 60 + minute > 3:
                before3min_task = Task(
                    datetime.datetime.now().replace(microsecond=0)
                    + datetime.timedelta(hours=hour, minutes=minute-3),
                    disconnect_task.members,
                    Task.BEFORE_3MIN)
                hq.heappush(self.tasks, before3min_task)

            await ctx.send(f"{disconnect_task.datetime}に"
                    + f"{', '.join(map(lambda m: m.display_name, disconnect_task.members))}を切断します")


def setup(bot):
    bot.add_cog(CmdCog(bot))
