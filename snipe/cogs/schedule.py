import discord
import asyncio
import re
from discord.ext import commands
from datetime import datetime, time, timedelta
from ..task import Task
from ..emoji import ALARM_CLOCK, TIMER_CLOCK


class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.vc = {}
        self.time_pattern = r"(?:(?P<hour>\d{1,2})(?:時間|時|:|：|hours|hour|h|Hours|Hour|H|\s^@))?"\
                            + r"(?:(?P<minute>\d{1,2})(?:分|mins|min|m|Mins|Min|M|))?"

    @commands.Cog.listener()
    async def on_ready(self):
        self.tasks = self.bot.tasks
        self.vc = self.bot.vc
        print("schedule cog is ready.")

    async def add_task(self, message, hour, minute, absolute=True):
        members =  set(filter(lambda m: not m.bot and m.status != discord.Status.offline,
                              message.channel.members)) \
                   if message.mention_everyone else \
                   set(filter(lambda m: m.id != self.bot.user.id, message.mentions))

        now = datetime.now(self.bot.timezone)

        if absolute:
            _minute = int(minute) if minute else 0
            _hour = int(hour) if hour else now.hour if _minute > now.minute else (now.hour + 1)

            disconnect_task = Task(
                now.replace(hour=0, minute=0, second=0)
                + timedelta(
                    days=int(_hour < 24 and time(hour=_hour, minute=_minute) < now.time()),
                    hours=_hour, minutes=_minute),
                members | set([message.author]),
                Task.DISCONNECT)
        else:
            _hour = int(hour) if hour else 0
            _minute = int(minute) if minute else 0

            disconnect_task = Task(
                now + timedelta(hours=_hour, minutes=_minute),
                members | set([message.author]),
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

        if not self.bot.loop.is_running():
            self.bot.loop.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        # 自身の場合は無視
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message):
            content = re.sub(r"^<@!?\d+>\s+", "", message.content)
            if match := re.match(self.time_pattern, content):
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
    async def reserve(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.match(self.time_pattern, t):
            if not any(match.group("hour", "minute")):  return

            hour, minute =  match.group("hour", "minute")

            await self.add_task(message=ctx.message, hour=hour, minute=minute, absolute=True)

    @commands.command()
    async def reservein(self, ctx, *args):
        t = " ".join(map(str, args))
        if match := re.match(self.time_pattern, t):
            if not any(match.group("hour", "minute")):  return

            hour, minute =  match.group("hour", "minute")

            await self.add_task(message=ctx.message, hour=hour, minute=minute, absolute=False)


def setup(bot):
    bot.add_cog(ScheduleCog(bot))
