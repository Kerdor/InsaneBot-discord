import os

from typing import Optional

import disnake
from disnake.ext import commands

bot = commands.Bot(command_prefix="/", help_command=None, intents=disnake.Intents.all(), test_guilds=[519209364280573954])

# кнопки
class Confirm(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.value = Optional[bool]

    @disnake.ui.button(label = "Confirm", style = disnake.ButtonStyle.green, emoji="🌒")
    async def confirm(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
        await inter.response.send_message("дарова")
        self.value = True
        self.stop()

    @disnake.ui.button(label = "Cancel", style = disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
        await inter.response.send_message("ok")
        self.value = False
        self.stop()

class Link(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(disnake.ui.Button(label = "заходи", url = "https://youtube.com"))

@bot.command(name = "party")
async def ask_party(ctx):
    view = Confirm()

    await ctx.send("дарова", view=view)
    await view.wait()

    if view.value is None:
        await ctx.send("проебался")
    elif view.value is True:
        await ctx.send("держи ссылку", view = Link())
    elif view.value is False:
        await ctx.send("жаль")

# выпадающее меню

class Dropdown(disnake.ui.StringSelect):

    def __init__(self):
        options = [
            disnake.SelectOption(label = "1", description="123")
        ]

        super().__init__(
            placeholder = "menu",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_message("++")

class DropdownView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())

@bot.command(name="drop")
async def order(ctx):
    await ctx.send("выбери", view=DropdownView())


# при заходе пользователя

@bot.event
async def on_member_join(member):
    role = disnake.utils.get(member.guild.roles, id = 519209664156532736)
    channel = member.guild.system_channel

    embed = disnake.Embed(
        title = "Новый участник",
        description = f"{member.name}#{member.discriminator}",
        color = 0xffffff,
    )
    await member.add_roles(role)
    await channel.send(embed=embed)


# список запрещенных слов

CENSORED_WORDS = {
    "пидор"
}

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    for content in message.content.split():
        for censored_word in CENSORED_WORDS:
            if content.lower() == censored_word:
                await message.delete()
                await message.channel.send(f"{message.author.mention} не пиши такое")


# команды модерации
@bot.command()
@commands.has_permissions(kick_members=True, administrator=True)
async def kick(ctx,member: disnake.Member, *, reason="Нарушение правил"):
    await ctx.send(f"{ctx.author.mention} исключил пользователя {member.mention}", delete_after=2)
    await member.kick(reason=reason)
    await ctx.message.delete()


#обработчик ошибок

@bot.event
async def on_command_error(ctx, error):
    print(error)

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author}, у вас недостаточно прав для выполнения данной команды!")
    elif isinstance(error, commands.UserInputError):
        await ctx.send(embed = disnake.Embed(
            description = f"Правильное использование команды: '{ctx.prefix}{ctx.command.name}' ({ctx.command.brief})"
        ))



bot.run("MTMyOTg2MzY5NzM1ODc4MjUwNA.GGWaJ0._VNwllQl6SF83UB6KWwTBnKoIM-FiEcrEuuwHc")