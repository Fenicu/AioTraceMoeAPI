import asyncio
import datetime as dt
import os.path

from aiotracemoeapi import TraceMoe, types

api = TraceMoe()


async def search_anime(path: str, url: bool):
    anime = await api.search(path, is_url=url)
    parse_text(anime)


def parse_text(anime_response: types.AnimeResponse):
    if isinstance(anime_response.best_result.anilist, types.AniList):
        if len(anime_response.best_result.anilist.title) > 0:
            print("Title:")
            for k, v in anime_response.best_result.anilist.title.items():
                if v is None:
                    continue
                print(f"{k}: {v}")
            print(f"My Anime List: {anime_response.best_result.anilist.mal_url}")
        if len(anime_response.best_result.anilist.synonyms) > 0:
            print("Synonyms:")
            for syn in anime_response.best_result.anilist.synonyms:
                print(syn)
        if anime_response.best_result.anilist.is_adult:
            print("Hentai🔞")
    if anime_response.best_result.episode:
        episode = anime_response.best_result.episode
        if isinstance(anime_response.best_result.episode, list):
            episode = " | ".join(str(ep) for ep in anime_response.best_result.episode)
        print(f"Episode: {episode}")
    if anime_response.best_result.anime_from:
        print(
            f"Starting time of the matching scene: {dt.timedelta(seconds=int(anime_response.best_result.anime_from))}"
        )
    print(f"Similarity: {anime_response.best_result.short_similarity()}")


if __name__ == "__main__":
    path = os.path.join(os.path.abspath("."), "pics", "bleach.jpg")
    url = False
    if not os.path.isfile(path):
        path = "https://s1.zerochan.net/Kurosaki.Ichigo.600.172225.jpg"
        url = True
    loop = asyncio.get_event_loop()
    loop.run_until_complete(search_anime(path, url))
