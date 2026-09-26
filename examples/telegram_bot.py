# /// script
# requires-python = ">=3.10"
# dependencies = ["aiogram>=3.20,<4", "aiotracemoeapi>=4.0"]
# ///
"""
Telegram bot that finds the anime of a screenshot, built with aiogram 3.

    BOT_TOKEN=123:abc uv run examples/telegram_bot.py

Send the bot a screenshot (as a photo or as an image file) and it replies with the anime,
episode, timestamp and a preview clip. Set TRACE_MOE_KEY to use your trace.moe API key.
"""

import asyncio
import html
import logging
import os
from datetime import timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from aiotracemoeapi import AnimeSearch, SearchQuotaDepleted, TraceMoe, TraceMoeAPIError

dp = Dispatcher()


def caption(match: AnimeSearch) -> str:
    anilist = match.anilist_info
    title = (anilist.title.english or anilist.title.romaji or anilist.title.native) if anilist else None
    lines = [f"<b>{html.escape(title or f'AniList #{match.anilist_id}')}</b>"]
    if match.episode_start is not None:
        lines.append(f"Episode {match.episode_start}")
    at = match.at if match.at is not None else match.anime_from
    lines.append(f"At {timedelta(seconds=int(at))}, similarity {match.short_similarity()}")
    if anilist:
        lines.append(f'<a href="{anilist.url}">AniList</a>')
    if match.similarity < 0.9:
        lines.append("<i>Low similarity, this may be a wrong result</i>")
    return "\n".join(lines)


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer("Send me an anime screenshot and I will find where it is from.")


@dp.message(F.photo | F.document.mime_type.startswith("image/"))
async def on_image(message: Message, bot: Bot, api: TraceMoe) -> None:
    file = message.photo[-1] if message.photo else message.document
    if file is None:
        return
    image = await bot.download(file)  # BytesIO
    if image is None:
        return

    try:
        response = await api.search(image)
    except SearchQuotaDepleted:
        await message.reply("Daily search limit reached, try again later.")
        return
    except TraceMoeAPIError as e:
        await message.reply(f"Search failed: {html.escape(str(e))}")
        return

    best = response.best_result
    if best is None:
        await message.reply("Nothing found.")
        return

    is_adult = best.anilist_info is not None and best.anilist_info.is_adult
    try:
        # Telegram downloads the preview itself; the URL is valid for 5 minutes
        await message.reply_video(best.video_url(size="l", mute=True), caption=caption(best), has_spoiler=is_adult)
    except Exception:
        logging.exception("Failed to send the preview video")
        await message.reply(caption(best))


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # One wrapper for the whole bot: keeps connections alive and retries when trace.moe is busy
    async with TraceMoe(token=os.getenv("TRACE_MOE_KEY"), max_retries=3) as api:
        await dp.start_polling(bot, api=api)


if __name__ == "__main__":
    asyncio.run(main())
