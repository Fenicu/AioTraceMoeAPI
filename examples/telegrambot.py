import datetime as dt
import io

from aiogram import Bot, Dispatcher, executor, md, types
from aiotracemoeapi import TraceMoe
from aiotracemoeapi.types import AniList

API_TOKEN = "BOT TOKEN HERE"

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

trace_bot = TraceMoe()


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("You can Send / Forward anime screenshots to me.")


@dp.message_handler(
    chat_type=[types.ChatType.PRIVATE],
    content_types=[types.ContentType.PHOTO],
    run_task=True,
)
async def search_anime_private(message: types.Message):
    msg = await message.answer("Search...")
    pic = io.BytesIO()

    try:
        pic = await message.photo[-1].download(pic)
        anime = await trace_bot.search(pic)
    except Exception:
        await msg.edit_text(r"Ooops ¯\_(ツ)_/¯")
        return

    out = str()

    if isinstance(anime.best_result.anilist, AniList):
        if len(anime.best_result.anilist.title) > 0:
            out += f"{md.hlink('Title:', anime.best_result.anilist.mal_url)}\n"
            for k, v in anime.best_result.anilist.title.items():
                if v is None:
                    continue
                out += f"  {k}: {v}\n"

        if len(anime.best_result.anilist.synonyms) > 0:
            out += "Synonyms:\n"
            for syn in anime.best_result.anilist.synonyms:
                out += f"  {syn}\n"

    if anime.best_result.anilist.is_adult:
        out += "Hentai🔞\n"

    if anime.best_result.episode:
        out += f"Episode: {md.hbold(str(anime.best_result.episode))}\n"

    if anime.best_result.anime_from:
        out += f"Starting time of the matching scene: {md.hbold(str(dt.timedelta(seconds=int(anime.best_result.anime_from))))}\n"

    out += f"Similarity: {md.hbold(anime.best_result.short_similarity())}\n"

    await msg.edit_text(out)
    await message.chat.do(types.ChatActions.UPLOAD_VIDEO)
    await message.reply_video(anime.best_result.video)


@dp.message_handler(
    commands="wait",
    chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP],
    is_reply=True,
    run_task=True,
)
async def search_anime_in_group(message: types.Message, reply: types.Message):
    allow_list = [types.ContentType.PHOTO]
    if reply.content_type not in allow_list:
        await message.answer("This is not a screenshot")
        return
    await search_anime_private(reply)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
