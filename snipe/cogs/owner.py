import discord
import traceback
from discord.ext import commands
from ..task import Task


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.tasks = self.bot.tasks
        print("owner cog is ready.")

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

    @commands.command()
    @commands.is_owner()
    async def reload(self, _, c):
        cog = "snipe.cogs." + c
        try:
            self.bot.reload_extension(cog)
        except Exception:
            print("Failed to load extension:", cog)
            traceback.print_exc()


def setup(bot):
    bot.add_cog(OwnerCog(bot))


def teardown(_):
    print("owner cog is unloaded.")
