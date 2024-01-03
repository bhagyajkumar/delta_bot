from typing import Union, List
from dotenv import load_dotenv
import discord
from discord import Message
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from cogs import tags

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = "A Discord bot to serve class notes and study materials."


class DeltaHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self) -> None:
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page, color=discord.Color.green())
            await destination.send(embed=emby)


class DeltaBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.motor_client = AsyncIOMotorClient(
            os.environ.get("MONGO_URL"))
        self.database = self.motor_client.get_database("deltaBot")
        super().__init__(command_prefix=self.get_prefix, intents=intents, *args, **kwargs)

    async def get_prefix(self, message: Message, /) -> Union[List[str], str]:
        query = await self.database.serverPrefixes.find_one({"_id": message.guild.id})
        if query is None:
            await self.database.serverPrefixes.insert_one(
                {"_id": message.guild.id, "prefix": "?"}
            )
            return "/"
        return [query["prefix"], ]


bot = DeltaBot()
bot.help_command = DeltaHelpCommand()


@bot.event
async def on_ready():
    try:
        await bot.motor_client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    await bot.load_extension("cogs.tags")
    await bot.load_extension("cogs.prefix")





bot.run(os.environ.get("BOT_TOKEN"))
