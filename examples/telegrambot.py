import datetime as dt
import io

from aiogram import Bot, Dispatcher, executor, md, types
from aiotracemoeapi import TraceMoe
from aiotracemoeapi.types import AniList

API_TOKEN = 'BOT TOKEN HERE'

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

trace_bot = TraceMoe()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("You can Send / Forward anime screenshots to me.")


@dp.message_handler(
    chat_type=[types.ChatType.PRIVATE],
    content_types=[types.ContentType.PHOTO],
    run_task=True
)
async def search_anime_private(message: types.Message):
    msg = await message.answer("Search...")
    pic = io.BytesIO()

    try:
        pic = await message.photo[-1].download(pic)
        anime_response = await trace_bot.search(pic)
    except Exception:
        await msg.edit_text(r"Ooops ¯\_(ツ)_/¯")
        return

    best_result = anime_response.result[0]
    out = str()

    if isinstance(best_result.anilist, AniList):
        if len(best_result.anilist.title) > 0:
            out += f"{md.hlink('Title:', best_result.anilist.mal_url)}\n"
            for k, v in best_result.anilist.title.items():
                if v is None:
                    continue
                out += f"  {k}: {v}\n"

        if len(best_result.anilist.synonyms) > 0:
            out += "Synonyms:\n"
            for syn in best_result.anilist.synonyms:
                out += f"  {syn}\n"

    if best_result.anilist.is_adult:
        out += "Hentai🔞\n"

    if best_result.episode:
        out += f"Episode: {md.hbold(str(best_result.episode))}\n"

    if best_result.afrom:
        out += f"Starting time of the matching scene: {md.hbold(str(dt.timedelta(seconds=int(best_result.afrom))))}\n"

    out += "Similarity: <b>{:.1%}</b>\n".format(best_result.similarity)

    await msg.edit_text(out)
    await message.chat.do(types.ChatActions.UPLOAD_VIDEO)
    await message.reply_video(best_result.video)


@dp.message_handler(
    commands="wait",
    chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP],
    is_reply=True,
    run_task=True
)
async def search_anime_in_group(message: types.Message, reply: types.Message):
    allow_list = [types.ContentType.PHOTO]
    if reply.content_type not in allow_list:
        await message.answer("This is not a screenshot")
        return
    await search_anime_private(reply)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
