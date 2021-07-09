import discord
import asyncio
import re
from discord.ext import commands
from discord_slash.utils.manage_components import (
        create_button, create_actionrow, wait_for_component)
from discord_slash import ButtonStyle, ComponentContext
from datetime import datetime, time, timedelta
from ..task import Task
from ..emoji import ALARM_CLOCK, TIMER_CLOCK


class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.vc = {}
        self.buttons = [
            create_button(style=ButtonStyle.green, label="時刻", custom_id="snipe_absolute", emoji=ALARM_CLOCK),
            create_button(style=ButtonStyle.blue, label="時間後", custom_id="snipe_relative", emoji=TIMER_CLOCK)
        ]
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

        if not self.bot.execute.is_running():
            self.bot.execute.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        # 自身の場合は無視
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message):
            content = re.sub(r"^<@!?\d+>\s+", "", message.content)
            if match := re.match(self.time_pattern, content):
                if not any(match.group("hour", "minute")):  return

                select_msg = await message.reply("時間指定方法の選択", components=[create_actionrow(*self.buttons)])

                try:
                    btn_ctx: ComponentContext = await wait_for_component(
                            self.bot, components=self.buttons, timeout=60)
                except asyncio.TimeoutError:
                    print("timeout")
                    await select_msg.delete()
                    await message.reply("タイムアウトしました")
                    return

                await select_msg.delete()

                hour, minute = match.group("hour", "minute")
                if btn_ctx.custom_id == "snipe_absolute":
                    await self.add_task(message=message, hour=hour, minute=minute, absolute=True)
                elif btn_ctx.custom_id == "snipe_relative":
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
