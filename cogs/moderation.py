from discord.ext import commands
import re


forbidden_words = r'\b(nigger.|nigger)\b'


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    # Deleting Messages
    @commands.command()
    async def purge(self, ctx, limit: int):
        """
            Usage: s!purge <number_of_messages>
            Deletes the specified number of messages from the channel.
            Max limit is 100 messages.
        """
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

        def is_me(m):
            return m.author == self.bot.user
            
        # If a check is not provided then all messages are deleted without discrimination.
        # deleted = await ctx.channel.purge(limit=limit, check=is_me)
        deleted = await ctx.channel.purge(limit=limit+1)  # for deleting all messages
        msg = await ctx.channel.send(f'Deleted {len(deleted)-1} message(s)')
        await msg.delete(delay=3)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send(f"Welcome to the server {member.name}")


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