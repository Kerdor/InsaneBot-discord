from __future__ import annotations

from io import BytesIO

import disnake
from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _color(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    try:
        value = value.strip().lstrip("#")
        if len(value) != 6:
            return fallback
        return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))
    except ValueError:
        return fallback


async def generate_profile_card(
    member: disnake.Member,
    stats: dict[str, int],
    customization: dict[str, str] | None = None,
) -> BytesIO:
    width, height = 1000, 460
    customization = customization or {}
    background = _color(customization.get("background_color", "#181B23"), (24, 27, 35))
    accent = _color(customization.get("accent_color", "#FFD75A"), (255, 215, 90))
    bio = customization.get("bio", "").strip()

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 14, height), fill=accent)

    try:
        avatar_bytes = await member.display_avatar.read()
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB").resize((220, 220))
        mask = Image.new("L", (220, 220), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
        image.paste(avatar, (70, 100), mask)
    except (OSError, disnake.HTTPException):
        draw.ellipse((70, 100, 290, 320), outline=accent, width=4)

    title_font = _font(42)
    label_font = _font(24)
    value_font = _font(32)
    small_font = _font(20)
    bio_font = _font(18)

    draw.text((340, 45), member.display_name, font=title_font, fill=(255, 255, 255))
    draw.text((340, 105), f"Уровень {stats['level']}", font=value_font, fill=accent)
    draw.text((340, 160), f"XP: {stats['progress']}/{stats['required']}  |  Всего: {stats['xp']}", font=label_font, fill=(210, 215, 225))
    draw.text((340, 230), f"Монеты: {stats['balance']:,}".replace(",", " "), font=label_font, fill=(255, 255, 255))
    draw.text((650, 230), f"Редкая валюта: {stats['rare_currency']}", font=label_font, fill=(255, 255, 255))
    draw.text((340, 290), f"Сообщений: {stats['messages']}", font=small_font, fill=(190, 195, 205))
    draw.text((650, 290), f"XP за голос: {stats['voice_xp']}", font=small_font, fill=(190, 195, 205))
    draw.text((340, 335), f"Достижений: {stats['achievements']}", font=small_font, fill=(190, 195, 205))

    if bio:
        draw.text((340, 385), bio[:70], font=bio_font, fill=(220, 220, 225))

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output
