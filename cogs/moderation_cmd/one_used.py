from __future__ import annotations

import logging
from typing import Iterable, Tuple

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)


SECTIONS: Tuple[Tuple[str, str], ...] = (
    (
        "1 - Общее положение",
        (
            "1.1 - Данные правила являются обязательными для ознакомления. Незнание правил не освобождает Вас от ответственности.\n"
            "1.2 - Правила могут быть изменены и дополнены в любое время.\n"
            "1.3 - За нарушение нижеперечисленных правил следует наказание по усмотрению администрации.\n"
            "1.4 - Администрация имеет право выдать наказание за действия, не упоминающиеся в правилах и на которые была подана жалоба.\n"
            "1.5 - В список правил сервера также входит список [правил Discord](https://discord.com/guidelines)."
        ),
    ),
    (
        "2 - Основные правила",
        (
            "2.1 - Запрещено упоминать родных любого из пользователей в оскорбительном контексте.\n"
            "2.2 - Запрещено выводить других пользователей/администраторов на конфликт.\n"
            "2.3 - Запрещено упоминать/рекламировать посторонние ресурсы/проекты.\n"
            "2.4 - Запрещено распространять любую ложную информацию.\n"
            "2.5 - Запрещено цитировать личную переписку без явного согласия обеих сторон.\n"
            "2.6 - Запрещено обсуждать и публично осуждать действия администрации.\n"
            "2.7 - Запрещено дискриминировать человека по какому-либо признаку.\n"
            "2.8 - Запрещено пропагандировать различные религиозные организации.\n"
            "2.9 - Запрещено разглашение любой персональной информации пользователей данного сервера без их личного разрешения.\n"
            "2.10 - Запрещено любое упоминание религиозных тем и их оскорбление.\n"
            "2.11 - Запрещено демонстрировать или пропагандировать деятельность, символику или обозначения экстремистских организаций, включая запрещённые в РФ."
        ),
    ),
    (
        "3 - Аккаунт",
        (
            "3.1 - Запрещено размещать в профиле/никнейме рекламные ссылки на сторонние ресурсы/проекты.\n"
            "3.2 - Запрещено иметь никнейм с оскорблением других пользователей/администраторов.\n"
            "3.3 - Запрещено дублировать никнейм другого пользователя.\n"
            "3.4 - Запрещено использовать аватары порнографического, экстремистского характера или содержащие фашистскую символику."
        ),
    ),
    (
        "4 - Текстовый чат",
        (
            "4.1 - Запрещено писать сообщения сплошными заглавными буквами (капсить).\n"
            "4.2 - Сообщения должны соответствовать тематике канала.\n"
            "4.3 - Запрещено часто отправлять однотипные сообщения, меняя только отдельные слова.\n"
            "4.4 - Запрещено публиковать материалы грубого, жестокого, порнографического или насильственного характера.\n"
            "4.5 - Запрещено публиковать экстремистские или расистские сообщения, а также литературу, пропагандирующую нацизм или фашизм."
        ),
    ),
)

def build_rule_embeds() -> Iterable[disnake.Embed]:
    for title, description in SECTIONS:
        embed = disnake.Embed(color=0x2F3136)
        embed.add_field(name=title, value=description, inline=False)
        yield embed

class OneUsedCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name="rules", description="Отправить правила сервера в чат")
    async def rules_slash(self, inter: disnake.ApplicationCommandInteraction) -> None:
        try:
            await inter.response.defer(ephemeral=True)
            
            embeds_sent = 0
            for embed in build_rule_embeds():
                try:
                    await inter.channel.send(embed=embed)
                    embeds_sent += 1
                except disnake.Forbidden:
                    await inter.followup.send("У меня нет прав для отправки сообщений в этот канал.", ephemeral=True)
                    return
                except disnake.HTTPException as e:
                    logger.exception("Failed to send rules embed: %s", e)
                    await inter.followup.send("Произошла ошибка при отправке правил.", ephemeral=True)
                    return

            try:
                rules_path = config.ensure_asset(config.ASSETS["rules_image"])
                file = disnake.File(rules_path, filename=rules_path.name)
                embed = disnake.Embed(color=0x2F3136)
                embed.set_image(url=f"attachment://{rules_path.name}")
                await inter.channel.send(embed=embed, file=file)
            except FileNotFoundError as e:
                logger.error("Rules image not found: %s", e)
                await inter.followup.send("Изображение с правилами не найдено.", ephemeral=True)
                return
            except disnake.Forbidden:
                await inter.followup.send("У меня нет прав для отправки файлов в этот канал.", ephemeral=True)
                return
            except disnake.HTTPException as e:
                logger.exception("Failed to send rules image: %s", e)
                await inter.followup.send("Произошла ошибка при отправке изображения правил.", ephemeral=True)
                return

            if embeds_sent > 0:
                await inter.followup.send("Правила отправлены.", ephemeral=True)
            else:
                await inter.followup.send("Не удалось отправить правила.", ephemeral=True)
        except Exception as e:
            logger.exception("Unexpected error in rules command: %s", e)
            try:
                await inter.followup.send("Произошла непредвиденная ошибка.", ephemeral=True)
            except Exception:
                pass  # Если не можем отправить ответ, просто логируем ошибку

    @commands.command(name="rules", help="Отправить правила сервера в чат.")
    async def rules_prefix(self, ctx: commands.Context) -> None:
        """Отправляет правила сервера (префиксная команда)."""
        try:
            for embed in build_rule_embeds():
                try:
                    await ctx.send(embed=embed)
                except disnake.Forbidden:
                    await ctx.send("У меня нет прав для отправки сообщений в этот канал.")
                    return
                except disnake.HTTPException as e:
                    logger.exception("Failed to send rules embed: %s", e)
                    await ctx.send("Произошла ошибка при отправке правил.")
                    return

            try:
                rules_path = config.ensure_asset(config.ASSETS["rules_image"])
                file = disnake.File(rules_path, filename=rules_path.name)
                embed = disnake.Embed(color=0x2F3136)
                embed.set_image(url=f"attachment://{rules_path.name}")
                await ctx.send(embed=embed, file=file)
            except FileNotFoundError as e:
                logger.error("Rules image not found: %s", e)
                await ctx.send("Изображение с правилами не найдено.")
            except disnake.Forbidden:
                await ctx.send("У меня нет прав для отправки файлов в этот канал.")
            except disnake.HTTPException as e:
                logger.exception("Failed to send rules image: %s", e)
                await ctx.send("Произошла ошибка при отправке изображения правил.")
        except Exception as e:
            logger.exception("Unexpected error in rules command: %s", e)
            await ctx.send("Произошла непредвиденная ошибка.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OneUsedCommands(bot))
