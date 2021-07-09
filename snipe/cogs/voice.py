import discord
from discord.ext import commands


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = {}
        self.vc = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.tasks = self.bot.tasks
        print("voice cog is ready.")

    @commands.command()
    async def connect(self, ctx):
        print("call connect()")
        if ctx.author.voice and self.tasks[ctx.guild.id]:
            self.vc[ctx.guild.id] = await ctx.author.voice.channel.connect()
            self.vc[ctx.guild.id].play(discord.FFmpegPCMAudio("snipe/sounds/connect.wav"), after=lambda _: print("connected"))

    @commands.command()
    async def disconnect(self, ctx):
        print("call disconnect()")
        _vc = self.vc[ctx.guild.id]
        if _vc and _vc.is_connected():
            await _vc.disconnect()


def setup(bot):
    bot.add_cog(VoiceCog(bot))
