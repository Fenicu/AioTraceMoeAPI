"""
Search by MPEG-7 ColorLayout vectors instead of uploading images.

    uv run examples/vector_search.py
    uv run examples/vector_search.py gwebWzth7oPe2UIubOJmozi1NDFp <another hash> ...

A vector is 33 numbers describing the colors of a frame. It is much smaller than an image,
so searching by vector is faster and saves bandwidth. Extract it with the official
trace.moe-id library (https://github.com/soruly/trace.moe-id) and pass either
the base64 hash from ColorLayout.encode() or the list of 33 numbers.
Each vector costs 1 search credit; a batch can hold up to 10 vectors.
"""

import asyncio
import os
import sys

from aiotracemoeapi import TraceMoe

EXAMPLE_VECTOR = "gwebWzth7oPe2UIubOJmozi1NDFp"


async def main() -> None:
    vectors = sys.argv[1:] or [EXAMPLE_VECTOR]

    async with TraceMoe(token=os.getenv("TRACE_MOE_KEY")) as api:
        if len(vectors) == 1:
            response = await api.search_vector(vectors[0])
            best_results = [response.best_result]
        else:
            batch = await api.search_vectors(vectors)
            best_results = batch.best_results

    for vector, best in zip(vectors, best_results, strict=True):
        if best is None:
            print(f"{vector}: no matches")
            continue
        title = best.anilist_info.title.romaji if best.anilist_info else f"AniList #{best.anilist_id}"
        at = best.at if best.at is not None else best.anime_from
        print(f"{vector}: {best.short_similarity()} {title}, episode {best.episode_start}, at {at:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
