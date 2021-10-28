import datetime as dt
import io
import json
from asyncio.exceptions import TimeoutError
from typing import Optional, Tuple

from aiogram import Bot, Dispatcher, executor, md, types
from aioredis import Redis

from aiotracemoeapi import TraceMoe, exceptions
from aiotracemoeapi.types import AniList, AnimeResponse

API_TOKEN = "BOT TOKEN HERE"

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

trace_bot = TraceMoe(timeout=10)


class SimpleStorage:
    def __init__(self):
        self._redis = None

    async def get_db(self) -> Redis:
        if self._redis is None:
            self._redis = await Redis(
                host="localhost",
                max_connections=10,
                decode_responses=True,
                db=6,
            )
        return self._redis

    async def check_in_cache(self, file_id: str) -> Optional[AnimeResponse]:
        redis = await self.get_db()

        addr = f"anime:{file_id}"
        _anime = await redis.get(addr)
        if _anime is None:
            return None

        anime = json.loads(_anime)
        return AnimeResponse(**anime)

    async def add_in_cache(self, file_id, data: AnimeResponse):
        redis = await self.get_db()
        addr = f"anime:{file_id}"
        await redis.set(addr, data.json(by_alias=True), ex=dt.timedelta(weeks=1))

    async def close(self):
        if self._redis:
            await self._redis.close()


storage = SimpleStorage()


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("You can Send / Forward anime screenshots to me.")


@dp.message_handler(
    chat_type=types.ChatType.PRIVATE,
    content_types=[
        types.ContentType.PHOTO,
        types.ContentType.ANIMATION,
        types.ContentType.VIDEO,
    ],
    run_task=True,
)
async def search_anime(message: types.Message, send_nsfw: bool = True):
    try:
        download = None
        if message.content_type in types.ContentTypes.VIDEO:
            download = message.video.download
            file_id = message.video.file_unique_id
        elif message.content_type in types.ContentTypes.ANIMATION:
            download = message.animation.download
            file_id = message.animation.file_unique_id
        elif message.content_type in types.ContentTypes.PHOTO:
            download = message.photo[-1].download
            file_id = message.photo[-1].file_unique_id
        else:
            await message.reply("This file type is not supported")
            return

        msg = await message.reply("Search...")
        anime = await storage.check_in_cache(file_id)

        if not anime:
            data = io.BytesIO()
            await download(destination_file=data)
            anime = await trace_bot.search(data)
            await storage.add_in_cache(file_id, anime)

    except exceptions.SearchQueueFull:
        await msg.edit_text("Search queue is full, try again later")

    except exceptions.SearchQuotaDepleted:
        await msg.edit_text("Monthly search limit reached")

    except exceptions.TraceMoeAPIError as error:
        await msg.edit_text(f"Unexpected error:\n{error.text}")

    except TimeoutError:
        await msg.edit_text("Server timed out. Try again later")

    except Exception as error:
        await msg.edit_text(f"Unknown error\n{error}")

    else:
        out, kb = parse_text(anime)
        await msg.edit_text(out, disable_web_page_preview=True, reply_markup=kb)
        if (not anime.best_result.anilist.is_adult) or (anime.best_result.anilist.is_adult and send_nsfw):
            await message.chat.do(types.ChatActions.UPLOAD_VIDEO)
            await msg.reply_video(anime.best_result.video)


@dp.message_handler(
    commands="wait",
    chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP],
    is_reply=True,
    run_task=True,
)
async def search_anime_in_group(message: types.Message, reply: types.Message):
    await search_anime(message=reply, send_nsfw=False)


def parse_text(anime_response: AnimeResponse) -> Tuple[str, types.InlineKeyboardMarkup]:
    out = str()
    kb = types.InlineKeyboardMarkup()
    if isinstance(anime_response.best_result.anilist, AniList):
        if len(anime_response.best_result.anilist.title) > 0:
            out += "Title:\n"
            kb.add(
                types.InlineKeyboardButton(
                    "My Anime List", url=anime_response.best_result.anilist.mal_url
                )
            )
            for k, v in anime_response.best_result.anilist.title.items():
                if v is None:
                    continue
                out += f"  {k}: {v}\n"
        if len(anime_response.best_result.anilist.synonyms) > 0:
            out += "Synonyms:\n"
            for syn in anime_response.best_result.anilist.synonyms:
                out += f"  {syn}\n"
        if anime_response.best_result.anilist.is_adult:
            out += "Hentai🔞\n"
    if anime_response.best_result.episode:
        episode = anime_response.best_result.episode
        if isinstance(anime_response.best_result.episode, list):
            episode = " | ".join(str(ep) for ep in anime_response.best_result.episode)
        out += f"Episode: {md.hbold(str(episode))}\n"
    if anime_response.best_result.anime_from:
        out += f"Starting time of the matching scene: {md.hbold(str(dt.timedelta(seconds=int(anime_response.best_result.anime_from))))}\n"
    out += f"Similarity: {md.hbold(anime_response.best_result.short_similarity())}\n"
    return out, kb


async def on_startup(dp: Dispatcher):
    bot_me = await dp.bot.me
    tm_me = await trace_bot.me()
    print(f"Bot @{bot_me.username} starting")
    print(f"You have {tm_me.quota_used}/{tm_me.quota} anime search queries left")


async def on_shutdown(dp: Dispatcher):
    await storage.close()


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
