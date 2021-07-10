import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from datetime import datetime, time, timedelta
from collections import deque
from ..task import Task
import re


class SlashCmdCog(commands.Cog):
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
        print("slash command cog is ready.")

    async def add_task(self, ctx, hour, minute, absolute=True):
        now = datetime.now(self.bot.timezone)

        if absolute:
            _minute = int(minute) if minute else 0
            _hour = int(hour) if hour else now.hour if _minute > now.minute else (now.hour + 1)

            disconnect_task = Task(
                now.replace(hour=0, minute=0, second=0)
                + timedelta(
                    days=int(_hour < 24 and time(hour=_hour, minute=_minute) < now.time()),
                    hours=_hour, minutes=_minute),
                set([ctx.author]),
                Task.DISCONNECT)
        else:
            _hour = int(hour) if hour else 0
            _minute = int(minute) if minute else 0

            disconnect_task = Task(
                now + timedelta(hours=_hour, minutes=_minute),
                set([ctx.author]),
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

        insert_task(self.tasks[ctx.guild_id], disconnect_task)

        if disconnect_task.datetime - now > timedelta(minutes=3):
            before3min_task = Task(
                disconnect_task.datetime - timedelta(minutes=3),
                disconnect_task.members,
                Task.BEFORE_3MIN)
            insert_task(self.tasks[ctx.guild_id], before3min_task)

        await ctx.send(f"{disconnect_task.datetime.strftime('%m-%d %H:%M:%S')}に"
                       + f"{ctx.author.mention}を切断します")

        if not self.bot.execute.is_running():
            self.bot.execute.start()

    @cog_ext.cog_slash(name="reserve", description="指定した時刻に通話を強制切断します",
            options=[
                create_option(
                    name="time",
                    description="切断する時刻",
                    option_type=3,
                    required=True)]
            )
    async def reserve(self, ctx: SlashContext, time: str):
        if match := re.match(self.time_pattern, time):
            if not any(match.group("hour", "minute")):  return

            hour, minute =  match.group("hour", "minute")

            await self.add_task(ctx=ctx, hour=hour, minute=minute, absolute=True)

    @cog_ext.cog_slash(name="reservein", description="指定した時間後に通話を強制切断します",
            options=[
                create_option(
                    name="time",
                    description="切断する時間",
                    option_type=3,
                    required=True)]
            )
    async def reservein(self, ctx: SlashContext, time: str):
        print(time)
        if match := re.match(self.time_pattern, time):
            if not any(match.group("hour", "minute")):  return

            hour, minute =  match.group("hour", "minute")

            await self.add_task(ctx=ctx, hour=hour, minute=minute, absolute=False)

    @cog_ext.cog_slash(name="cancel", description="通話の切断予定をキャンセルします")
    async def cancel(self, ctx: SlashContext):
        def remove_members(task):
            task.members -= set([ctx.author])
            return task.members

        self.tasks[ctx.guild_id] = deque(filter(remove_members, self.tasks[ctx.guild_id]))
        await ctx.send(f"{ctx.author.mention}を予定から削除しました")

    @cog_ext.cog_slash(name="schedule", description="通話の切断予定を表示します")
    async def schedule(self, ctx: SlashContext):
        embed = discord.Embed(title="射殺予定", description="snipebotの通話切断予定表です")

        for task in self.tasks[ctx.guild_id]:
            embed.add_field(
                name=f"{'強制切断' if task.type == Task.DISCONNECT else '3分前連絡'}: "
                    + task.datetime.strftime("%m-%d %H:%M"),
                value=' '.join(map(lambda m: m.mention, task.members)))

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SlashCmdCog(bot))
