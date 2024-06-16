import discord
from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_balance(self, user_id):
        query = await self.bot.database.economy.find_one({'_id': user_id})
        if query is None:
            # Create a new entry if user doesn't exist in the database
            initial_data = {'_id': user_id, 'bankBalance': 0, 'walletBalance': 100}
            await self.bot.database.economy.insert_one(initial_data)
            return initial_data
        return query

    async def get_user_inventory(self, user_id):
        query = await self.bot.database.inventory.find_one({'_id': user_id})
        if query is None:
            # Create a new entry if user doesn't exist in the inventory collection
            initial_inventory = {'_id': user_id, 'items': []}
            await self.bot.database.inventory.insert_one(initial_inventory)
            return initial_inventory
        return query

    async def get_shop_items(self):
        return await self.bot.database.shop.find().to_list(length=None)

    async def get_work_by_name(self, work_name):
        return await self.bot.database.works.find_one({'name': work_name})

    @commands.command(aliases=['bal'])
    async def balance(self, ctx):
        """Check your balance in the wallet and bank."""
        user_data = await self.get_user_balance(ctx.author.id)

        embed = discord.Embed(title="Balance", color=discord.Color.blurple())
        embed.add_field(name="Wallet Balance", value=user_data['walletBalance'])
        embed.add_field(name="Bank Balance", value=user_data['bankBalance'])
        await ctx.send(embed=embed)

    @commands.command()
    async def deposit(self, ctx, amount: int):
        """Deposit money from your wallet to your bank."""
        user_data = await self.get_user_balance(ctx.author.id)
        if amount > user_data['walletBalance']:
            await ctx.send("You don't have enough money in your wallet to deposit.")
            return

        new_wallet_balance = user_data['walletBalance'] - amount
        new_bank_balance = user_data['bankBalance'] + amount

        await self.bot.database.economy.update_one({'_id': ctx.author.id}, {
            '$set': {'walletBalance': new_wallet_balance, 'bankBalance': new_bank_balance}})
        await ctx.send(f"Successfully deposited {amount} bucks to your bank!")

    @commands.command()
    async def withdraw(self, ctx, amount: int):
        """Withdraw money from your bank to your wallet."""
        user_data = await self.get_user_balance(ctx.author.id)
        if amount > user_data['bankBalance']:
            await ctx.send("You don't have enough money in your bank to withdraw.")
            return

        new_wallet_balance = user_data['walletBalance'] + amount
        new_bank_balance = user_data['bankBalance'] - amount

        await self.bot.database.economy.update_one({'_id': ctx.author.id}, {
            '$set': {'walletBalance': new_wallet_balance, 'bankBalance': new_bank_balance}})
        await ctx.send(f"Successfully withdrew {amount} bucks to your wallet!")

    @commands.command()
    async def works(self, ctx):
        """Display available works."""
        works = await self.bot.database.works.find().to_list(length=None)

        if not works:
            await ctx.send("No works available at the moment.")
            return

        embed = discord.Embed(title="Available Works", color=discord.Color.blurple())
        for work in works:
            embed.add_field(name=work['name'], value=f"Earnings: {work['earnings']} bucks", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def work(self, ctx, work_name: str):
        """Do a work to earn money."""
        work = await self.get_work_by_name(work_name)
        if not work:
            await ctx.send(f"{work_name} is not a valid work.")
            return

        user_inventory = await self.get_user_inventory(ctx.author.id)

        # Check if the user has the required item for this work
        if work['required_item'] not in user_inventory['items']:
            await ctx.send(f"You need a {work['required_item']} to perform this work.")
            return

        user_data = await self.get_user_balance(ctx.author.id)
        new_wallet_balance = user_data['walletBalance'] + work['earnings']
        await self.bot.database.economy.update_one({'_id': ctx.author.id},
                                                   {'$set': {'walletBalance': new_wallet_balance}})
        await ctx.send(f"You performed {work['name']} and earned {work['earnings']} bucks!")

    @commands.command()
    async def shop(self, ctx):
        """Display the items available in the shop."""
        shop_items = await self.get_shop_items()

        if not shop_items:
            await ctx.send("The shop is currently empty.")
            return

        embed = discord.Embed(title="Shop", color=discord.Color.blurple())
        for item in shop_items:
            embed.add_field(name=f"{item['name']} {item['emoji']}", value=f"Price: {item['price']} bucks", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, item_name: str):
        """Buy an item from the shop."""
        shop_items = await self.get_shop_items()
        item_to_buy = next((item for item in shop_items if item['name'].lower() == item_name.lower()), None)

        if not item_to_buy:
            await ctx.send(f"{item_name} is not available in the shop.")
            return

        user_data = await self.get_user_balance(ctx.author.id)
        if user_data['walletBalance'] < item_to_buy['price']:
            await ctx.send("You don't have enough money to buy this item.")
            return

        new_wallet_balance = user_data['walletBalance'] - item_to_buy['price']
        await self.bot.database.economy.update_one({'_id': ctx.author.id},
                                                   {'$set': {'walletBalance': new_wallet_balance}})

        # Add the item to the user's inventory
        user_inventory = await self.get_user_inventory(ctx.author.id)
        user_inventory['items'].append(item_to_buy['_id'])
        await self.bot.database.inventory.update_one({'_id': ctx.author.id},
                                                     {'$set': {'items': user_inventory['items']}})

        await ctx.send(f"Successfully bought {item_to_buy['name']} for {item_to_buy['price']} bucks!")

    @commands.command()
    @commands.is_owner()
    async def add_item(self, ctx, name: str,emoji: str, price: int):
        """Add a new item to the shop."""
        new_item = {'name': name, 'price': price, 'emoji': emoji}
        await self.bot.database.shop.insert_one(new_item)
        await ctx.send(f"Added {name}{emoji} to the shop with a price of {price} bucks.")

    @add_item.error
    async def add_item_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Please provide both a name and a price for the item.")
        await ctx.send(error)


    @commands.command()
    async def inventory(self, ctx):
        """Display the user's inventory."""
        user_inventory = await self.get_user_inventory(ctx.author.id)

        if not user_inventory['items']:
            await ctx.send("Your inventory is empty.")
            return

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Inventory", color=discord.Color.blurple())
        for item_id in user_inventory['items']:
            item_data = await self.bot.database.shop.find_one({'_id': item_id})
            embed.add_field(name=item_data['name'], value=f"Price: {item_data['price']} bucks", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
