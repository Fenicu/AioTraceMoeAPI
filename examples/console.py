import asyncio
import datetime as dt
import os.path

from aiotracemoeapi import TraceMoe, types

api = TraceMoe()
# or api = TraceMoe(token="ABC")


async def search_anime(path: str, url: bool):
    anime_response = await api.search(path, is_url=url)
    best_result = anime_response.result[0]
    if isinstance(best_result.anilist, types.AniList):
        print(f"Anime: {best_result.anilist.mal_url}")

        if len(best_result.anilist.title) > 0:
            print("Title:")
            for k, v in best_result.anilist.title.items():
                if v is None:
                    continue
                print(f"{k}: {v}")

        if len(best_result.anilist.synonyms) > 0:
            print("Synonyms:")
            for syn in best_result.anilist.synonyms:
                print(syn)

        if best_result.anilist.is_adult:
            print("Hentai 🔞!")

    if best_result.episode:
        print(f"Episode: {best_result.episode}")

    if best_result.afrom:
        print(f"Starting time of the matching scene: {str(dt.timedelta(seconds=int(best_result.afrom)))}")

    print("Similarity: {:.1%}".format(best_result.similarity))


if __name__ == "__main__":
    path = os.path.join(os.path.abspath("."), "pics", "bleach.jpg")
    url = False
    if not os.path.isfile(path):
        path = "https://s1.zerochan.net/Kurosaki.Ichigo.600.172225.jpg"
        url = True
    loop = asyncio.get_event_loop()
    loop.run_until_complete(search_anime(path, url))
