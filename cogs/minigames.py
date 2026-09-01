"""Skill-based mini-games that reuse the existing XP and economy systems."""

from __future__ import annotations

import asyncio
import logging
import random
import time

import disnake
from disnake.ext import commands

from databases.economy import add_balance, get_user as get_economy_user, init_economy
from databases.settings import get_bool, init_settings
from databases.xp import add_xp, init_xp

logger = logging.getLogger(__name__)


class MiniGameView(disnake.ui.View):
    """Base view for a single-user mini-game session."""

    def __init__(self, cog: "MiniGames", user_id: int, timeout: float = 20.0) -> None:
        super().__init__(timeout=timeout)
        self.cog = cog
        self.user_id = user_id
        self.finished = False

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        """Prevent other members from controlling the active player's game."""
        if inter.author.id != self.user_id:
            await inter.response.send_message("Это не твоя мини-игра.", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        """Finish an unanswered game without granting a reward."""
        if self.finished:
            return
        self.finished = True
        await self.cog._finish_timeout(self)


class MiniGames(commands.Cog):
    """Provide lightweight skill games with persistent XP and coin rewards."""

    REWARD_XP = 15
    REWARD_COINS = 25
    COOLDOWN = 30

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._cooldowns: dict[tuple[int, int], float] = {}
        self._active_games: set[tuple[int, int]] = set()
        init_xp()
        init_economy()
        init_settings()

    def _cooldown_remaining(self, guild_id: int, user_id: int) -> int:
        """Return whole seconds remaining on the player's mini-game cooldown."""
        remaining = self.COOLDOWN - (time.monotonic() - self._cooldowns.get((guild_id, user_id), 0.0))
        return max(0, int(remaining + 0.999))

    async def _finish_timeout(self, view: MiniGameView) -> None:
        """Remove an expired session from the active-game registry."""
        self._active_games.discard((view.cog._guild_id, view.user_id))
        for child in view.children:
            child.disabled = True

        if view.message:
            try:
                await view.message.edit(content="⏱️ Время вышло. Награда не получена.", view=view)
            except disnake.HTTPException:
                pass

    async def _reward(self, inter: disnake.MessageInteraction, view: MiniGameView) -> None:
        """Award the standard mini-game reward and settle the player's level."""
        guild_id = inter.guild.id
        user_id = inter.author.id
        self._active_games.discard((guild_id, user_id))
        self._cooldowns[(guild_id, user_id)] = time.monotonic()

        row = add_xp(guild_id, user_id, self.REWARD_XP)
        if get_bool(guild_id, "economy_enabled"):
            add_balance(guild_id, user_id, self.REWARD_COINS)

        xp_cog = self.bot.get_cog("XP")
        if xp_cog is not None:
            await xp_cog._apply_level(inter.guild, user_id, row)

        view.finished = True
        view.stop()
        for child in view.children:
            child.disabled = True

        economy = get_economy_user(guild_id, user_id)
        coins = int(economy["balance"]) if economy else 0
        await inter.response.edit_message(
            content=f"🎉 Победа! **+{self.REWARD_XP} XP** и **+{self.REWARD_COINS} 🪙**. Баланс: **{coins} 🪙**.",
            view=view,
        )

    @commands.slash_command(name="minigame", description="Сыграть в мини-игру и получить XP")
    async def minigame(
        self,
        inter: disnake.ApplicationCommandInteraction,
        game: str = commands.Param(
            choices=[
                disnake.OptionChoice("Математика", "math"),
                disnake.OptionChoice("Реакция", "reaction"),
                disnake.OptionChoice("Память", "memory"),
            ]
        ),
    ) -> None:
        """Start one of the available skill-based mini-games."""
        if not inter.guild:
            await inter.response.send_message("Мини-игры доступны только на сервере.", ephemeral=True)
            return
        if not get_bool(inter.guild.id, "xp_enabled"):
            await inter.response.send_message("XP отключён на этом сервере.", ephemeral=True)
            return

        key = (inter.guild.id, inter.author.id)
        remaining = self._cooldown_remaining(*key)
        if remaining:
            await inter.response.send_message(f"⏳ Попробуй снова через **{remaining} сек.**", ephemeral=True)
            return
        if key in self._active_games:
            await inter.response.send_message("У тебя уже есть активная мини-игра.", ephemeral=True)
            return

        self._active_games.add(key)
        self._cooldowns.pop(key, None)

        if game == "math":
            view = self._math_game(inter.author.id)
            text = "🧮 Реши пример и выбери правильный ответ."
        elif game == "reaction":
            view, text = self._reaction_game(inter.author.id)
        else:
            view, text = self._memory_game(inter.author.id)

        view._guild_id = inter.guild.id
        await inter.response.send_message(text, view=view)
        view.message = await inter.original_response()

    def _math_game(self, user_id: int) -> MiniGameView:
        """Build a short arithmetic challenge."""
        first = random.randint(5, 30)
        second = random.randint(2, 20)
        operation = random.choice(("+", "-", "×"))
        if operation == "+":
            answer = first + second
        elif operation == "-":
            answer = first - second
        else:
            answer = first * second

        options = {answer}
        while len(options) < 4:
            options.add(answer + random.randint(-10, 10))
        buttons = list(options)
        random.shuffle(buttons)
        view = MiniGameView(self, user_id)

        for value in buttons:
            button = disnake.ui.Button(label=str(value), style=disnake.ButtonStyle.secondary)

            async def callback(inter: disnake.MessageInteraction, value=value) -> None:
                if view.finished:
                    return
                if value != answer:
                    view.finished = True
                    self._active_games.discard((inter.guild.id, user_id))
                    self._cooldowns[(inter.guild.id, user_id)] = time.monotonic()
                    view.stop()
                    for child in view.children:
                        child.disabled = True
                    await inter.response.edit_message(content=f"❌ Неверно. Правильный ответ: **{answer}**.", view=view)
                    return
                await self._reward(inter, view)

            button.callback = callback
            view.add_item(button)

        view._answer_text = f"**{first} {operation} {second} = ?**"
        original_timeout = view.on_timeout

        async def timeout_with_answer() -> None:
            await original_timeout()

        view.on_timeout = timeout_with_answer
        return view

    def _reaction_game(self, user_id: int) -> tuple[MiniGameView, str]:
        """Build a button-position reaction challenge."""
        target = random.choice(("🔴", "🟢", "🔵", "🟡"))
        view = MiniGameView(self, user_id)
        values = ["🔴", "🟢", "🔵", "🟡"]
        random.shuffle(values)
        for value in values:
            button = disnake.ui.Button(label=value, style=disnake.ButtonStyle.secondary)

            async def callback(inter: disnake.MessageInteraction, value=value) -> None:
                if view.finished:
                    return
                if value != target:
                    view.finished = True
                    self._active_games.discard((inter.guild.id, user_id))
                    self._cooldowns[(inter.guild.id, user_id)] = time.monotonic()
                    view.stop()
                    for child in view.children:
                        child.disabled = True
                    await inter.response.edit_message(content=f"❌ Не тот цвет. Нужно было нажать **{target}**.", view=view)
                    return
                await self._reward(inter, view)

            button.callback = callback
            view.add_item(button)
        return view, f"⚡ Нажми на **{target}** быстрее остальных."

    def _memory_game(self, user_id: int) -> tuple[MiniGameView, str]:
        """Build a small sequence-memory challenge using buttons."""
        sequence = [str(random.randint(1, 4)) for _ in range(3)]
        view = MiniGameView(self, user_id, timeout=30.0)
        view.sequence = sequence
        view.position = 0

        for value in ("1", "2", "3", "4"):
            button = disnake.ui.Button(label=value, style=disnake.ButtonStyle.secondary)

            async def callback(inter: disnake.MessageInteraction, value=value) -> None:
                if view.finished:
                    return
                expected = view.sequence[view.position]
                if value != expected:
                    view.finished = True
                    self._active_games.discard((inter.guild.id, user_id))
                    self._cooldowns[(inter.guild.id, user_id)] = time.monotonic()
                    view.stop()
                    for child in view.children:
                        child.disabled = True
                    await inter.response.edit_message(content=f"❌ Ошибка. Последовательность была: **{' '.join(sequence)}**.", view=view)
                    return
                view.position += 1
                if view.position == len(view.sequence):
                    await self._reward(inter, view)
                    return
                await inter.response.edit_message(content=f"🧠 Верно! Следующее число — **#{view.position + 1}**.", view=view)

            button.callback = callback
            view.add_item(button)

        view._sequence_text = " ".join(sequence)
        return view, f"🧠 Запомни последовательность: **{' '.join(sequence)}**. Затем вводи её кнопками по порядку."

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        """Keep mini-game sessions isolated from normal message progression."""
        if message.guild and message.author.bot:
            return


def setup(bot: commands.Bot) -> None:
    """Register the mini-games cog."""
    bot.add_cog(MiniGames(bot))
    logger.info("MiniGames cog loaded")
