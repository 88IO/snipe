import discord
from discord.ext import commands
from ..task import Task


class ShowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.tasks = self.bot.tasks
        print("show cog is ready.")

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
    @commands.is_owner()
    async def showall(self, ctx):
        for guild_id, tasks in self.tasks.items():
            _guild = await self.bot.fetch_guild(guild_id)
            embed = discord.Embed(title=_guild.name, description=_guild.id)

            for task in tasks:
                embed.add_field(
                    name=f"{'強制切断' if task.type == Task.DISCONNECT else '3分前連絡'}: "
                        + task.datetime.strftime("%m-%d %H:%M"),
                    value=' '.join(map(lambda m: m.mention, task.members)))

            await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(ShowCog(bot))
