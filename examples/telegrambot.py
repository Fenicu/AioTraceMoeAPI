import datetime as dt
import io
from typing import Tuple

from aiogram import Bot, Dispatcher, executor, md, types
from aiotracemoeapi import TraceMoe
from aiotracemoeapi.types import AniList, AnimeResponse

API_TOKEN = "BOT TOKEN HERE"

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

trace_bot = TraceMoe()


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
async def search_anime(message: types.Message):
    msg = await message.answer("Search...")
    try:
        data = io.BytesIO()
        if message.content_type in types.ContentTypes.VIDEO:
            data = await message.video.download(destination_file=data)
        elif message.content_type in types.ContentTypes.ANIMATION:
            data = await message.animation.download(destination_file=data)
        elif message.content_type in types.ContentTypes.PHOTO:
            data = await message.photo[-1].download(destination_file=data)
        else:
            await message.answer("This file type is not supported")
            return
        anime = await trace_bot.search(data)
    except Exception:
        await msg.edit_text(r"Ooops ¯\_(ツ)_/¯")
        return

    out, kb = parse_text(anime)
    await msg.edit_text(out, disable_web_page_preview=True, reply_markup=kb)
    if not anime.best_result.anilist.is_adult:
        await message.chat.do(types.ChatActions.UPLOAD_VIDEO)
        await message.reply_video(anime.best_result.video)


@dp.message_handler(
    commands="wait",
    chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP],
    is_reply=True,
    run_task=True,
)
async def search_anime_in_group(message: types.Message, reply: types.Message):
    allow_list = [
        types.ContentType.PHOTO,
        types.ContentType.ANIMATION,
        types.ContentType.VIDEO,
    ]
    if reply.content_type not in allow_list:
        await message.answer("This is not a screenshot")
        return
    await search_anime(reply)


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


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
