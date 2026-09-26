"""
Search every image in a folder and save the results to a CSV file.

    uv run examples/batch_folder.py ./screenshots results.csv

Searches run in parallel up to your account's concurrency limit, and temporary errors
(busy server, concurrency limit) are retried automatically.
Set the TRACE_MOE_KEY environment variable to use your API key.
"""

import argparse
import asyncio
import csv
import os
from pathlib import Path

from aiotracemoeapi import AnimeResponse, TraceMoe, TraceMoeAPIError

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".mp4", ".webm", ".mkv"}


async def search_one(api: TraceMoe, limiter: asyncio.Semaphore, path: Path) -> AnimeResponse | Exception:
    async with limiter:
        try:
            return await api.search(path, anilist_info=True)
        except TraceMoeAPIError as e:
            return e


async def main() -> None:
    parser = argparse.ArgumentParser(description="Search all images in a folder")
    parser.add_argument("folder", type=Path)
    parser.add_argument("output", type=Path, nargs="?", default=Path("results.csv"))
    args = parser.parse_args()

    files = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if not files:
        raise SystemExit(f"No images in {args.folder}")

    async with TraceMoe(token=os.getenv("TRACE_MOE_KEY"), max_retries=5) as api:
        me = await api.me()
        if me.quota_left < len(files):
            print(f"Warning: {len(files)} files, but only {me.quota_left} searches left today")

        limiter = asyncio.Semaphore(me.concurrency)
        results = await asyncio.gather(*(search_one(api, limiter, path) for path in files))

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "similarity", "anilist_id", "title", "episode", "at_seconds", "error"])
        for path, result in zip(files, results, strict=True):
            if isinstance(result, Exception):
                writer.writerow([path.name, "", "", "", "", "", str(result)])
                print(f"{path.name}: error: {result}")
                continue

            best = result.best_result
            if best is None:
                writer.writerow([path.name, "", "", "", "", "", "no matches"])
                continue

            title = best.anilist_info.title.romaji if best.anilist_info else ""
            writer.writerow(
                [path.name, f"{best.similarity:.4f}", best.anilist_id, title, best.episode_start, best.at, ""]
            )
            print(f"{path.name}: {best.short_similarity()} {title}")

    print(f"\nSaved {len(files)} results to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
