import disnake
from disnake.ext import commands
import datetime



class chat_logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        channel_chat_logs = self.bot.get_channel(1330604289957302350)
        member = message.author

        if(message.author != self.bot.user):
            embed_logs = disnake.Embed(
                title="New message",
                color=0xffffff,
                timestamp=datetime.datetime.now()
            )
            embed_logs.add_field(name="Author", value=f"{member.mention}", inline=True)
            embed_logs.add_field(name="text", value=f"{message.content}")
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed_logs.set_thumbnail(url=avatar_url)

            await channel_chat_logs.send(embed=embed_logs)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        channel_chat_logs = self.bot.get_channel(1330604289957302350)
        member = message.author

        if(message.author != self.bot.user):
            embed_logs = disnake.Embed(
                title="Delete message",
                color=0xffffff,
                timestamp=datetime.datetime.now()
            )
            embed_logs.add_field(name="Author", value=f"{member.mention}", inline=True)
            embed_logs.add_field(name="Text", value=f"{message.content}")
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed_logs.set_thumbnail(url=avatar_url)

            await channel_chat_logs.send(embed=embed_logs)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        channel_chat_logs = self.bot.get_channel(1330604289957302350)

        if(before.author != self.bot.user):
            embed_logs = disnake.Embed(
                title="Edit message",
                color=0xffffff,
                timestamp=datetime.datetime.now()
            )
            embed_logs.add_field(name="Author", value=f"{before.author.mention}", inline=True)
            embed_logs.add_field(name="Before", value=f"{before.content}")
            embed_logs.add_field(name="After", value=f"{after.content}")
            avatar_url = before.author.avatar.url if before.author.avatar else before.author.default_avatar.url
            embed_logs.set_thumbnail(url=avatar_url)

            await channel_chat_logs.send(embed=embed_logs)
        

def setup(bot):
    bot.add_cog(chat_logs(bot))