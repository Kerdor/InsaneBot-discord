import disnake
from disnake.ext import commands

class SelectGames(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label="Dota 2", value="1332487694252638320"),
            disnake.SelectOption(label="CS 2", value="1332487739932934165"),
            disnake.SelectOption(label="PAYDAY 2", value="1332487809600323624"),   
        ]
        super().__init__(placeholder="Выбери игры", options=options, custom_id="games", min_values=0, max_values=3)
    
    async def callback(self, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        all_roles = {1332487694252638320, 1332487739932934165, 1332487809600323624}
        to_remove = []
        to_add = []

        if not interaction.values:
            for role_id in all_roles:
                role = interaction.guild.get_role(role_id)
                to_remove.append(role)
            await interaction.author.remove_roles(*to_remove, reason="Удалены все роли")

        else:
            chosen_roles = {int(value) for value in interaction.values}
            ids_to_remove = all_roles - chosen_roles

            for role_id in ids_to_remove:
                role = interaction.guild.get_role(role_id)
                to_remove.append(role)

            for role_id in chosen_roles:
                role = interaction.guild.get_role(role_id)
                to_add.append(role)
            
            await interaction.author.remove_roles(*to_remove, reason="Роли удалены")
            await interaction.author.add_roles(*to_add, reason="Роли добавлены")

class GameRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistents_views_added = False

    @commands.slash_command()
    async def games(self, ctx):
        view = disnake.ui.View(timeout=None)
        view.add_item(SelectGames())
        await ctx.send("Выбери свою игру", view=view)

        @commands.Cog.listener()
        async def on_connets(self):
            if self.persistents_views_added:
                return
            
            view = disnake.ui.View(timeout=None)
            view.add_item(SelectGames())
            self.bot_add_view(view, message_id=1332628998379012100)


def setup(bot):
    bot.add_cog(GameRoles(bot))
