from __future__ import annotations

from io import BytesIO

import disnake
from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


async def generate_profile_card(member: disnake.Member, stats: dict[str, int]) -> BytesIO:
    width, height = 1000, 420
    image = Image.new("RGB", (width, height), (24, 27, 35))
    draw = ImageDraw.Draw(image)

    try:
        avatar_bytes = await member.display_avatar.read()
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB").resize((220, 220))
        mask = Image.new("L", (220, 220), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
        image.paste(avatar, (70, 100), mask)
    except (OSError, disnake.HTTPException):
        draw.ellipse((70, 100, 290, 320), outline=(255, 255, 255), width=4)

    title_font = _font(42)
    label_font = _font(24)
    value_font = _font(32)
    small_font = _font(20)

    draw.text((340, 55), member.display_name, font=title_font, fill=(255, 255, 255))
    draw.text((340, 115), f"Уровень {stats['level']}", font=value_font, fill=(255, 215, 90))
    draw.text((340, 170), f"XP: {stats['progress']}/{stats['required']}  |  Всего: {stats['xp']}", font=label_font, fill=(210, 215, 225))
    draw.text((340, 240), f"Монеты: {stats['balance']:,}".replace(",", " "), font=label_font, fill=(255, 255, 255))
    draw.text((650, 240), f"Редкая валюта: {stats['rare_currency']}", font=label_font, fill=(255, 255, 255))
    draw.text((340, 300), f"Сообщений: {stats['messages']}", font=small_font, fill=(190, 195, 205))
    draw.text((650, 300), f"XP за голос: {stats['voice_xp']}", font=small_font, fill=(190, 195, 205))
    draw.text((340, 350), f"Достижений: {stats['achievements']}", font=small_font, fill=(190, 195, 205))

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output
