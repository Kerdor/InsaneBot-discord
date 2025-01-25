import disnake
from disnake.ext import commands

from config import config

bot = commands.Bot(command_prefix="/", help_command=None, intents=disnake.Intents.all(), test_guilds=[519209364280573954])

@bot.event
async def on_ready():
        print(f"Bot {bot.user} is ready to work!")



@bot.slash_command()
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Коги **{extension}** успешно подгружены.", ephemeral=True)
    except:
        await ctx.send("Произошла ошибка!", ephemeral=True)

@bot.slash_command()
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"Коги **{extension}** успешно выгружены.", ephemeral=True)
    except:
        await ctx.send("Произошла ошибка!", ephemeral=True)

@bot.slash_command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"Коги **{extension}** успешно перезагружены.", ephemeral=True)
    except:
        await ctx.send("Произошла ошибка!", ephemeral=True)



cogs_list = [
    "cogs.moderation_cmd",
    "cogs.user_cmd"
]

# Коги для модерации
bot.load_extension(f"{cogs_list[0]}.moderation")
bot.load_extension(f"{cogs_list[0]}.chat_logs")


# Коги для пользователей
bot.load_extension(f"{cogs_list[1]}.get_roles")



bot.run(config["token"])