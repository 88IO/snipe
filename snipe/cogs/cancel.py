from discord.ext import commands
from collections import deque


class CancelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.tasks = self.bot.tasks
        print("cancel cog is ready.")

    @commands.command()
    async def clear(self, ctx):
        members = set(filter(lambda m: m.id != self.bot.user.id, ctx.message.mentions)) | set([ctx.author])

        def remove_members(task):
            task.members -= members
            return task.members

        self.tasks[ctx.guild.id] = deque(filter(remove_members, self.tasks[ctx.guild.id]))
        await ctx.reply(f"{', '.join(map(lambda m: m.mention, members))}を予定から削除しました")


def setup(bot):
    bot.add_cog(CancelCog(bot))
