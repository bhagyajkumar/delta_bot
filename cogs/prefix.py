from discord.ext import commands


class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        mention = f'<@{self.bot.user.id}>'
        if message.content == mention:
            query = await self.bot.database.serverPrefixes.find_one({"_id": message.guild.id})
            if query is None:
                await message.reply("My prefix for this server is `?`")
            await message.reply(f"My prefix for this server is `{query['prefix']}`")

    @commands.command(name="setprefix", aliases=["sp"])
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx, prefix: str):
        """
        Set a prefix for the bot for this server
        """
        await self.bot.database.serverPrefixes.update_one({"_id": ctx.guild.id}, {"$set": {"prefix": prefix}})
        await self.bot.redis.hset('server_prefixes', str(ctx.guild.id), prefix)
        await ctx.reply(f"The prefix for this server is updated to `{prefix}")




async def setup(bot):
    await bot.add_cog(Prefix(bot))
