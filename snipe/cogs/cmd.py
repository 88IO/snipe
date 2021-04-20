from discord.ext import commands, tasks
import discord
import asyncio
import heapq as hq
from datetime import datetime, time, timezone, timedelta
import re
from ..task import Task
from ..emoji import ALARM_CLOCK, TIMER_CLOCK


class CmdCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.JST = timezone(timedelta(hours=+9), 'JST')
        self.tasks = []
        self.vc = None

    @tasks.loop(seconds=3)
    async def loop(self):
        print(self.tasks)

        while self.tasks and self.tasks[0].datetime <= datetime.now(self.JST):
            task = hq.heappop(self.tasks)
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
                        if self.vc and self.vc.is_connected():
                            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/3min.wav"))
                        try:
                            await member.send("3分後に通話を強制切断します")
                        except discord.errors.HTTPException:
                            pass

        if not self.tasks:
            self.loop.stop()

    async def add_task(self, message, hour, minute, absolute=True):
        now = datetime.now(self.JST)

        if absolute:
            hour = now.hour if hour is None else int(hour)
            minute = now.minute if minute is None else int(minute)

            disconnect_task = Task(
                now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                + timedelta(
                    days=int(time(hour=hour, minute=minute) < now.time())),
                set(filter(lambda m: m.id != self.bot.user.id, message.mentions)) | set([message.author]),
                Task.DISCONNECT)

        else:
            hour = int(hour) if hour else 0
            minute = int(minute) if minute else 0
            disconnect_task = Task(
                now.replace(microsecond=0)
                + timedelta(hours=hour, minutes=minute),
                set(filter(lambda m: m.id != self.bot.user.id, message.mentions)) | set([message.author]),
                Task.DISCONNECT)
        hq.heappush(self.tasks, disconnect_task)

        if disconnect_task.datetime - now > timedelta(minutes=3):
            before3min_task = Task(
                disconnect_task.datetime - timedelta(minutes=3),
                disconnect_task.members,
                Task.BEFORE_3MIN)
            hq.heappush(self.tasks, before3min_task)

        await message.reply(f"{disconnect_task.datetime.strftime('%m-%d %H:%M:%S')}に"
                + f"{', '.join(map(lambda m: m.display_name, disconnect_task.members))}を切断します")

        if not self.loop.is_running():
            self.loop.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        # 自身の場合は無視
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message):
            content = re.sub(r"^<@!?\d+>\s+", "", message.content)
            if match := re.match(r"(?:(?P<hour>\d{1,2})(?:時間|時|:|：|hours|hour|h|Hours|Hour|H|\s^@))?"\
                                 + r"(?:(?P<minute>\d{1,2})(?:分|mins|min|m|Mins|Min|M|))?", content):
                if not any(match.group("hour", "minute")):  return

                # アラーム絵文字（絶対）
                await message.add_reaction(ALARM_CLOCK)
                # タイマー絵文字（相対）
                await message.add_reaction(TIMER_CLOCK)

                def reaction_check(reaction, user):
                    return user == message.author and reaction.emoji in [ALARM_CLOCK, TIMER_CLOCK]

                try:
                    reaction, _ = await self.bot.wait_for("reaction_add", timeout=60, check=reaction_check)
                except asyncio.TimeoutError:
                    print("timeout")
                    await message.reply("タイムアウトしました")
                    return

                await message.remove_reaction(ALARM_CLOCK, self.bot.user)
                await message.remove_reaction(TIMER_CLOCK, self.bot.user)

                hour, minute = match.group("hour", "minute")
                if reaction.emoji == ALARM_CLOCK:
                    await self.add_task(message=message, hour=hour, minute=minute, absolute=True)

                elif reaction.emoji == TIMER_CLOCK:
                    await self.add_task(message=message, hour=hour, minute=minute, absolute=False)

    @commands.command()
    async def show(self, ctx):
        embed = discord.Embed(title="射殺予定", description="snipebotの通話切断予定表です")
        for task in sorted(self.tasks):
            embed.add_field(
                name=f"{'強制切断' if task.type == Task.DISCONNECT else '3分前連絡'}: "
                       + task.datetime.strftime("%m-%d %H:%M"),
                value=' '.join(map(lambda m: m.mention, task.members)))
        await ctx.reply(embed=embed)

    @commands.command()
    async def clear(self, ctx):
        members = set(ctx.message.mentions) | set([ctx.author])

        def remove_members(task):
            task.members -= members
            return task.members

        self.tasks = list(filter(remove_members, self.tasks))
        await ctx.reply(f"{', '.join(map(lambda m: m.display_name, members))}を予定から削除しました")

    @commands.command()
    async def connect(self, ctx):
        if ctx.author.voice:
            self.vc = await ctx.author.voice.channel.connect()
            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/connect.wav"), after=lambda _: print("connected"))

    @commands.command()
    async def disconnect(self, ctx):
        print("call disconnect()")
        if self.vc and self.vc.is_connected():
            self.vc.play(discord.FFmpegPCMAudio("snipe/sounds/disconnect.wav"), after=lambda _: print("disconnected"))
            await self.vc.disconnect()

    @commands.command()
    async def reserve(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.match(r"(?:(?P<hour>\d{1,2})(?:時間|時|:|：|hours|hour|h|Hours|Hour|H|\s^@))?"\
                                + r"(?:(?P<minute>\d{1,2})(?:分|mins|min|m|Mins|Min|M|))?", t):
            if not any(match.group("hour", "minute")):  return

            hour, minute =  match.group("hour", "minute")

            await self.add_task(message=ctx.message, hour=hour, minute=minute, absolute=True)

    @commands.command()
    async def reservein(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.match(r"(?:(?P<hour>\d{1,2})(?:時間|時|:|：|hours|hour|h|Hours|Hour|H|\s^@))?"\
                                + r"(?:(?P<minute>\d{1,2})(?:分|mins|min|m|Mins|Min|M|))?", t):
            if not any(match.group("hour", "minute")):  return

            hour, minute =  match.group("hour", "minute")

            await self.add_task(message=ctx.message, hour=hour, minute=minute, absolute=False)


def setup(bot):
    bot.add_cog(CmdCog(bot))
