from discord.ext import commands
import re


forbidden_words = r'\b(nigger.|nigger)\b'


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    def is_favorite(self, ctx):
        return not any(getattr(r.emoji, 'name', r.emoji) in ["⭐","star"] for r in ctx.reactions)

    async def limit_check(self, ctx, limit: int):
        if limit > 100:
                temp = await ctx.channel.send("Max Purge limit is 100 messages, are you sure you want to continue deleting 100 messages?")
                print("inisde Moderation!")
                confirmation = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=15.0)
                if not confirmation.content.lower() in ['yes', 'y', 'yeah', 'sure', 'a']:
                    await temp.delete(delay=3)
                    await ctx.send("Purge cancelled.", delete_after=3)
                    return
                await temp.delete(delay=3)
                limit = 100

    async def delete_message(self, ctx, limit: int, check=None):
        if check and self.is_favorite.__name__ == 'is_favorite':
            deleted = await ctx.channel.purge(limit=limit+1, check=check)  # for deleting specific messages
        else:
            deleted = await ctx.channel.purge(limit=limit+1)
        msg = await ctx.channel.send(f'Deleted {len(deleted)-1} message(s)')
        await msg.delete(delay=3)

    # Deleting Messages
    @commands.command()
    async def purge(self, ctx, limit: int):
        """
            Usage: s!purge <number_of_messages>
            Deletes the specified number of NON FAVORITE messages from the channel.
            Max limit is 100 messages.
        """
        await self.limit_check(ctx, limit)

        # def is_me(m):
        #     return m.author == self.bot.user

        # If a check is not provided then all messages are deleted without discrimination.
        # deleted = await ctx.channel.purge(limit=limit, check=is_me)
        await self.delete_message(ctx, limit, self.is_favorite)

    @commands.command()
    async def purgeall(self, ctx, limit: int):
        """
            Usage: s!purge <number_of_messages>
            Deletes the specified number of messages from the channel.
            Max limit is 100 messages.
        """
        await self.limit_check(ctx, limit)
        await self.delete_message(ctx, limit)

    # @commands.Cog.listener()
    # async def on_member_join(self, member):
    #     await member.send(f"Welcome to the server {member.name}")


    @commands.Cog.listener()
    async def on_message(self, message):
        # print(ctx.guild.id)
        if message.author.bot:
            return
        
        if re.search(forbidden_words, message.content.lower()):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Nuh-uh", delete_after=3)
        
        # await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
