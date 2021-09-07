# <p align="center">AioTraceMoeAPI

<p align="center">A simple, but extensible Python implementation for the trace.moe API.


  * [Getting started.](#getting-started)
  * [Writing your first code](#writing-your-first-code)

## Getting started.
install from PyPi
```
$ python -m pip install aiotracemoeapi
```

## Writing your first code
```python
import asyncio
import datetime as dt
import os.path

from aiotracemoeapi import TraceMoe, types

api = TraceMoe()
# or api = TraceMoe(token="ABC")


async def search_anime(path: str, url: bool):
    anime = await api.search(path, is_url=url)
    if isinstance(anime.best_result.anilist, types.AniList):
        print(f"Anime: {anime.best_result.anilist.mal_url}")

        if len(anime.best_result.anilist.title) > 0:
            print("Title:")
            for k, v in anime.best_result.anilist.title.items():
                if v is None:
                    continue
                print(f"{k}: {v}")

        if len(anime.best_result.anilist.synonyms) > 0:
            print("Synonyms:")
            for syn in anime.best_result.anilist.synonyms:
                print(syn)

        if anime.best_result.anilist.is_adult:
            print("Hentai 🔞!")

    if anime.best_result.episode:
        print(f"Episode: {anime.best_result.episode}")

    if anime.best_result.anime_from:
        print(f"Starting time of the matching scene: {str(dt.timedelta(seconds=int(anime.best_result.anime_from)))}")

    print(f"Similarity: {anime.best_result.short_similarity()}")


if __name__ == "__main__":
    path = os.path.join(os.path.abspath("."), "pics", "bleach.jpg")
    url = False
    if not os.path.isfile(path):
        path = "https://s1.zerochan.net/Kurosaki.Ichigo.600.172225.jpg"
        url = True
    loop = asyncio.get_event_loop()
    loop.run_until_complete(search_anime(path, url))


```
