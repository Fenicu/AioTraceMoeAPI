"""
Search an anime scene from the command line.

    uv run examples/console.py https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg
    uv run examples/console.py screenshot.jpg --cut-borders both
    uv run examples/console.py screenshot.jpg --anilist-id 21034 --top 3

Set the TRACE_MOE_KEY environment variable to use your API key.
"""

import argparse
import asyncio
import os
from datetime import timedelta

from aiotracemoeapi import (
    AnimeSearch,
    ConcurrencyLimitExceeded,
    CutBorders,
    SearchQueueFull,
    SearchQuotaDepleted,
    TraceMoe,
    TraceMoeAPIError,
)

CUT_BORDERS = {"none": CutBorders.NONE, "cut": CutBorders.CUT, "both": CutBorders.BOTH}


def format_time(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def describe(result: AnimeSearch) -> str:
    if anilist := result.anilist_info:
        title = anilist.title.english or anilist.title.romaji or anilist.title.native or "Unknown title"
    else:
        title = f"AniList #{result.anilist_id}"

    match (result.episode_start, result.episode_end):
        case (None, _):
            episode = f"episode {result.episode} (from filename)" if result.episode is not None else "unknown episode"
        case (start, end) if start == end:
            episode = f"episode {start}"
        case (start, end):
            episode = f"episodes {start}-{end}"

    at = format_time(result.at if result.at is not None else result.anime_from)
    return f"{result.short_similarity():>6}  {title}, {episode}, at {at}"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Search an anime scene by screenshot")
    parser.add_argument("source", help="image URL or path to a local image / video / gif")
    parser.add_argument("--anilist-id", type=int, help="search only within this anime")
    parser.add_argument("--cut-borders", choices=CUT_BORDERS, default="cut", help="black borders mode (default: cut)")
    parser.add_argument("--top", type=int, default=1, help="how many results to show")
    args = parser.parse_args()

    try:
        async with TraceMoe(token=os.getenv("TRACE_MOE_KEY"), max_retries=3) as api:
            response = await api.search(
                args.source,
                anilist_id=args.anilist_id,
                cut_borders=CUT_BORDERS[args.cut_borders],
            )
    except FileNotFoundError:
        raise SystemExit(f"File not found: {args.source}") from None
    except SearchQuotaDepleted as e:
        raise SystemExit(f"Daily search quota depleted ({e.quota_used}/{e.quota}), try again later") from None
    except (ConcurrencyLimitExceeded, SearchQueueFull):
        raise SystemExit("trace.moe is busy right now, try again later") from None
    except TraceMoeAPIError as e:
        raise SystemExit(f"trace.moe error: {e}") from None

    print(f"Searched {response.frame_count:,} frames, quota used: {response.quota_used}/{response.quota}\n")

    if not response.result:
        print("No matches found.")
        return

    for match in response.result[: args.top]:
        print(describe(match))

    best = response.result[0]
    if best.similarity < 0.9:
        print("\nSimilarity below 90% is most likely a wrong result.")
    if anilist := best.anilist_info:
        print(f"\nAniList: {anilist.url}")
        if anilist.mal_url:
            print(f"MyAnimeList: {anilist.mal_url}")
    # Preview URLs expire in 5 minutes
    print(f"Preview: {best.video_url(size='l', mute=True)}")


if __name__ == "__main__":
    asyncio.run(main())
