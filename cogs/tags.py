from datetime import datetime

import discord
from discord.ext import commands


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, tag_name):
        """
            To display the contents of a tag on the server
        """
        result = await self.bot.database.serverTags.find_one(
            {"_id": ctx.guild.id, "tags.author_id": ctx.author.id},
            {"_id": 0, "tags": {"$elemMatch": {"tag_name": tag_name}}}
        )
        if result is None:
            return await ctx.send("Please initialize tag with `init` command")
        if "tags" in result.keys():
            embed = discord.Embed(
                title=result["tags"][0]["tag_name"],
                description=result["tags"][0]["tag_content"],
                color=discord.Colour.green()
            )
            return await ctx.send(embed=embed)

        await ctx.send("Tag not found")

    @tag.command(name="list")
    async def list_tags(self, ctx):
        """
            To list all the tags by the user
        """
        tags = []

        query = self.bot.database.serverTags.find(
            {"_id": ctx.guild.id, "tags.author_id": ctx.author.id},
            {"_id": 0, "tags": 1}
        )
        async for tag in query:
            tags.extend(tag.get("tags", []))
        embed = discord.Embed(
            title="Tags by {}".format(ctx.author.name),
            description=", ".join(i["tag_name"] for i in tags),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @tag.command(name="init")
    async def init_tags(self, ctx):
        """
            To initialize tags for the server. This is an one time process
        """
        query = await self.bot.database.serverTags.find_one({"_id": ctx.guild.id})
        if query is not None:
            await ctx.send('Tags already initialized')
        await self.bot.database.serverTags.insert_one({
            "_id": ctx.guild.id,
            "tags": [],
        })
        await ctx.send('Tags successfully initialized')

    @tag.command(name="create")
    async def create_tag(self, ctx, tag_name, *, tag_content):
        tag_data = {
            "user_id": ctx.author.id,
            "tag_name": tag_name,
            "tag_content": tag_content,
            "created_at": datetime.utcnow(),
            "author_id": ctx.author.id
        }
        result = await self.bot.database.serverTags.find_one(
            {"_id": ctx.guild.id, "tags.author_id": ctx.author.id},
            {"_id": 0, "tags": {"$elemMatch": {"tag_name": tag_name}}}
        )
        if result is None:
            result = {}
        if "tags" in result.keys():
            return await ctx.send("Tag Already exist")
        await self.bot.database.serverTags.update_one({"_id": ctx.guild.id}, {"$push": {"tags": tag_data}})
        await ctx.send('tag created successfully')


async def setup(bot):
    await bot.add_cog(Tags(bot))
