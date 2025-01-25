import disnake
from disnake.ext import commands
import datetime

moderation_roles = {
    "owner": 519209664748191759,
    "administator": 519209661535223808,
    "moderator": 519209662181277726,
    "helper": 519209663519129600
}

class CMDModers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    

    @commands.slash_command(name="kick", description="Выгнать пользователя с сервера")
    @commands.has_any_role(moderation_roles["owner"],
                           moderation_roles["administator"],
                           moderation_roles["moderator"])
    async def kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, *, reason = "Нарушение правил"):
        await inter.response.send_message(f"Пользователь {member.mention} был выгнан по причине: \"**{reason}**\"", ephemeral=True)
        await member.kick(reason=reason)

        # логгирование
        channel_logs = self.bot.get_channel(1330604583000473732)

        embed_kick = disnake.Embed(
            title="kick",
            color=0xffffff,
            timestamp=datetime.datetime.now()
        )
        embed_kick.add_field(name="Модератор", value=f"{inter.author.mention}", inline=True)
        embed_kick.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed_kick.add_field(name="Причина", value=reason, inline=True)

        avatar_url = inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url
        embed_kick.set_thumbnail(url=avatar_url)

        await channel_logs.send(embed=embed_kick)
    

    @commands.slash_command(name="ban", description="Заблокировать пользователя на сервере")
    @commands.has_any_role(moderation_roles["owner"],
                            moderation_roles["administator"])
    async def ban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User, *, reason = "Нарушение правил"):
        await inter.response.send_message(f"Пользователь {user.mention} был заблокирован по причине: \"**{reason}**\"", ephemeral=True)
        await inter.guild.ban(user, reason=reason)

        # логгирование
        channel_logs = self.bot.get_channel(1330604583000473732)

        embed_ban = disnake.Embed(
            title="ban",
            color=0xffffff,
            timestamp=datetime.datetime.now()
        )
        embed_ban.add_field(name="Модератор", value=f"{inter.author.mention}", inline=True)
        embed_ban.add_field(name="Пользователь", value=f"{user.mention}", inline=True)
        embed_ban.add_field(name="Причина", value=reason, inline=True)

        avatar_url = inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url
        embed_ban.set_thumbnail(url=avatar_url)

        await channel_logs.send(embed=embed_ban)

    @commands.slash_command(name="unban", description="Разблокировать пользователя на сервере")
    @commands.has_any_role(moderation_roles["owner"],
                           moderation_roles["administator"])
    async def unban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        await inter.response.send_message(f"Пользователь {user.mention} был разблокирован", ephemeral=True)
        await inter.guild.unban(user.id)

        # логгирование
        channel_logs = self.bot.get_channel(1330604583000473732)

        embed_ban = disnake.Embed(
            title="unban",
            color=0xffffff,
            timestamp=datetime.datetime.now()
        )
        embed_ban.add_field(name="Модератор", value=f"{inter.author.mention}", inline=True)
        embed_ban.add_field(name="Пользователь", value=f"{user.mention}", inline=True)

        avatar_url = inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url
        embed_ban.set_thumbnail(url=avatar_url)

        await channel_logs.send(embed=embed_ban)


    @commands.slash_command(aliases=["mute", "timeout"], description="Отправить пользователя подумать над своим поведением")
    @commands.has_any_role(moderation_roles["owner"],
                           moderation_roles["administator"],
                           moderation_roles["moderator"],
                           moderation_roles["helper"])
    async def mute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, *, 
                    duration: str = commands.Param(description="Длительность. Использовать один из вариантов: %d/%h/%m/%s"), 
                    reason: str = commands.Param(description='Причина наказания')):
        channel_logs = self.bot.get_channel(1330604583000473732)

        
        if str(duration).endswith("d"):
            time = datetime.timedelta(days=int(duration[:-1]))
        elif str(duration).endswith("h"):
            time = datetime.timedelta(hours=int(duration[:-1]))
        elif str(duration).endswith("m"):
            time = datetime.timedelta(minutes=int(duration[:-1]))
        elif str(duration).endswith("s"):
            time = datetime.timedelta(seconds=int(duration[:-1]))

        await inter.response.send_message(f"Пользователь {member.mention} был отправлен подумать над своим поведением на **{duration}** по причине: \"**{reason}**\"", ephemeral=True)
        await member.timeout(reason=reason, duration=time)

        # логгирование
        embed_mute = disnake.Embed(
            title="Timeout",
            color=0xffffff,
            timestamp=datetime.datetime.now()
        )
        embed_mute.add_field(name="Admin", value=f"{inter.author.mention}", inline=True)
        embed_mute.add_field(name="User", value=f"{member.mention}", inline=True)
        embed_mute.add_field(name="Reason", value=reason, inline=True)

        time = duration[:-1]
        if str(duration).endswith("d"):
            embed_mute.add_field(name="Duration", value=f"{datetime.timedelta(days=int(time))}", inline=True)
            time = datetime.datetime.now() + datetime.timedelta(days=int(time))
            untimeout_time = time.strftime('%d-%m-%Y %H:%M:%S')
            embed_mute.add_field(name="UnTimeout date", value=f"{untimeout_time}", inline=True)
        elif str(duration).endswith("h"):
            embed_mute.add_field(name="Duration", value=f"{datetime.timedelta(hours=int(time))}", inline=True)
            time = datetime.datetime.now() + datetime.timedelta(hours=int(time))
            untimeout_time = time.strftime('%d-%m-%Y %H:%M:%S')
            embed_mute.add_field(name="UnTimeout date", value=f"{untimeout_time}", inline=True)
        elif str(duration).endswith("m"):
            embed_mute.add_field(name="Duration", value=f"{datetime.timedelta(minutes=int(time))}", inline=True)
            time = datetime.datetime.now() + datetime.timedelta(minutes=int(time))
            untimeout_time = time.strftime('%d-%m-%Y %H:%M:%S')
            embed_mute.add_field(name="UnTimeout date", value=f"{untimeout_time}", inline=True)
        elif str(duration).endswith("s"):
            embed_mute.add_field(name="Duration", value=f"{datetime.timedelta(seconds=int(time))}", inline=True)
            time = datetime.datetime.now() + datetime.timedelta(seconds=int(time))
            untimeout_time = time.strftime('%d-%m-%Y %H:%M:%S')
            embed_mute.add_field(name="UnTimeout date", value=f"{untimeout_time}", inline=True)


        avatar_url = inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url
        embed_mute.set_thumbnail(url=avatar_url)

        await channel_logs.send(embed=embed_mute)
 

def setup(bot):
    bot.add_cog(CMDModers(bot))