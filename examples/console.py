import asyncio
import datetime as dt
import sys

from aiotracemoeapi import (
    ConcurrencyLimitExceeded,
    SearchQueueFull,
    SearchQuotaDepleted,
    TraceMoe,
    TraceMoeAPIError,
)


def format_time(seconds: float) -> str:
    return str(dt.timedelta(seconds=int(seconds)))


async def main(source: str) -> None:
    """Search for an anime scene by an image URL or a local file path."""
    print(f"Searching for: {source}")

    try:
        # Retry a few times if the server is busy or the concurrency limit is hit
        async with TraceMoe(max_retries=3) as api:
            response = await api.search(source)
    except SearchQuotaDepleted as e:
        print(f"Error: daily search quota depleted ({e.quota_used}/{e.quota}).")
        return
    except (ConcurrencyLimitExceeded, SearchQueueFull):
        print("Error: the server is busy, please try again later.")
        return
    except TraceMoeAPIError as e:
        print(f"API Error: {e}")
        return

    print(f"Searched {response.frame_count} frames, quota used: {response.quota_used}/{response.quota}")

    best = response.best_result
    if best is None:
        print("No matches found.")
        return

    print("\n--- Best Match ---")
    print(f"Similarity: {best.short_similarity()}")
    if best.similarity < 0.9:
        print("(similarity below 90% is most likely an incorrect result)")

    # AniList info is included by default (anilist_info=True)
    if anilist := best.anilist_info:
        title = anilist.title.english or anilist.title.romaji or anilist.title.native or "Unknown Title"
        print(f"Title: {title}")
        print(f"Is Adult: {'Yes' if anilist.is_adult else 'No'}")
        print(f"AniList: {anilist.url}")
        if anilist.mal_url:
            print(f"MyAnimeList: {anilist.mal_url}")
    else:
        print(f"AniList ID: {best.anilist_id}")

    if best.episode_start is not None:
        episodes = str(best.episode_start)
        if best.episode_end != best.episode_start:
            episodes += f"-{best.episode_end}"
        print(f"Episode: {episodes}")
    elif best.episode is not None:
        print(f"Episode (from filename): {best.episode}")

    print(f"Scene: {format_time(best.anime_from)} - {format_time(best.anime_to)}")
    if best.at is not None:
        print(f"Best frame at: {format_time(best.at)}")

    # Preview URLs expire in 5 minutes
    print(f"Image Preview: {best.image_url(size='l')}")
    print(f"Video Preview: {best.video_url(size='l', mute=True)}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg"))
