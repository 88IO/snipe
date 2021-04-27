import discord
import asyncio
import re
from discord.ext import commands, tasks
from datetime import datetime, time, timezone, timedelta
from itertools import chain
from collections import deque
from ..task import Task
from ..emoji import ALARM_CLOCK, TIMER_CLOCK


class CmdCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.JST = timezone(timedelta(hours=+9), 'JST')
        self.tasks = {}
        self.vc = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.tasks = {guild.id:deque() for guild in self.bot.guilds}
        self.vc = {guild.id:None for guild in self.bot.guilds}

        print("Finish Loading... ready...")
        await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing, name="https://github.com/88IO/snipe"))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.tasks[guild.id] = deque()
        self.vc[guild.id] = None

    @tasks.loop(seconds=3)
    async def loop(self):
        print(self.tasks)
        tasks_values = self.tasks.values()

        async def get_executable(guild_tasks):
            now = datetime.now(self.JST)

            executable_tasks = (guild_tasks.popleft() for task in guild_tasks if task.datetime <= now)

            return executable_tasks

        executable_tasks = chain.from_iterable(
                await asyncio.gather(*(get_executable(guild_tasks) for guild_tasks in tasks_values)))

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
                        #_vc = self.vc[member.guild.id]
                        #if _vc and _vc.is_connected():
                        #    _vc.play(discord.FFmpegPCMAudio("snipe/sounds/3min.wav"))
                        try:
                            await member.send("3分後に通話を強制切断します")
                        except discord.errors.HTTPException:
                            pass

        for guild_tasks in tasks_values:
            if len(guild_tasks):
                return

        self.loop.stop()

    async def add_task(self, message, hour, minute, absolute=True):
        now = datetime.now(self.JST)

        if absolute:
            _minute = int(minute) if minute else 0
            _hour = int(hour) if hour else now.hour if _minute > now.minute else (now.hour + 1)

            disconnect_task = Task(
                now.replace(hour=0, minute=0, second=0)
                + timedelta(
                    days=int(_hour < 24 and time(hour=_hour, minute=_minute) < now.time()),
                    hours=_hour, minutes=_minute),
                set(filter(lambda m: m.id != self.bot.user.id, message.mentions)) | set([message.author]),
                Task.DISCONNECT)
        else:
            _hour = int(hour) if hour else 0
            _minute = int(minute) if minute else 0

            disconnect_task = Task(
                now + timedelta(hours=_hour, minutes=_minute),
                set(filter(lambda m: m.id != self.bot.user.id, message.mentions)) | set([message.author]),
                Task.DISCONNECT)

        def insert_task(tasks, new):
            for i, t in enumerate(tasks):
                if new == t:
                    t.members |= new.members
                    return
                elif new < t:
                    tasks.insert(i, new)
                    return
            tasks.append(new)

        insert_task(self.tasks[message.guild.id], disconnect_task)

        if disconnect_task.datetime - now > timedelta(minutes=3):
            before3min_task = Task(
                disconnect_task.datetime - timedelta(minutes=3),
                disconnect_task.members,
                Task.BEFORE_3MIN)
            insert_task(self.tasks[message.guild.id], before3min_task)

        await message.reply(f"{disconnect_task.datetime.strftime('%m-%d %H:%M:%S')}に"
                + f"{', '.join(map(lambda m: m.mention, disconnect_task.members))}を切断します")

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
                    return (user == message.author
                            and reaction.message == message
                            and reaction.emoji in [ALARM_CLOCK, TIMER_CLOCK])

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

        for task in self.tasks[ctx.guild.id]:
            embed.add_field(
                name=f"{'強制切断' if task.type == Task.DISCONNECT else '3分前連絡'}: "
                    + task.datetime.strftime("%m-%d %H:%M"),
                value=' '.join(map(lambda m: m.mention, task.members)))

        await ctx.reply(embed=embed)

    @commands.command()
    async def clear(self, ctx):
        members = set(filter(lambda m: m.id != self.bot.user.id, ctx.message.mentions)) | set([ctx.author])

        def remove_members(task):
            task.members -= members
            return task.members

        self.tasks[ctx.guild.id] = deque(filter(remove_members, self.tasks[ctx.guild.id]))
        await ctx.reply(f"{', '.join(map(lambda m: m.mention, members))}を予定から削除しました")

    @commands.command()
    async def connect(self, ctx):
        print("call connect()")
        if ctx.author.voice:
            self.vc[ctx.guild.id] = await ctx.author.voice.channel.connect()
            self.vc[ctx.guild.id].play(discord.FFmpegPCMAudio("snipe/sounds/connect.wav"), after=lambda _: print("connected"))

    @commands.command()
    async def disconnect(self, ctx):
        print("call disconnect()")
        _vc = self.vc[ctx.guild.id]
        if _vc and _vc.is_connected():
            _vc.play(discord.FFmpegPCMAudio("snipe/sounds/disconnect.wav"), after=lambda _: print("disconnected"))
            await _vc.disconnect()

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
