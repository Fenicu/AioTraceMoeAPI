"""
Find a scene and download its preview image and video clip.

    uv run examples/download_preview.py https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg
    uv run examples/download_preview.py screenshot.jpg --output ./previews

Preview URLs expire in 5 minutes, so download them right after the search.
Previews do not use your search quota.
"""

import argparse
import asyncio
import os
from pathlib import Path

import httpx

from aiotracemoeapi import TraceMoe


async def download(client: httpx.AsyncClient, url: str, path: Path) -> None:
    async with client.stream("GET", url) as response:
        response.raise_for_status()
        with path.open("wb") as f:
            async for chunk in response.aiter_bytes():
                f.write(chunk)
    print(f"Saved {path}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Download previews of the best match")
    parser.add_argument("source", help="image URL or path to a local image")
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Share one HTTP client between the API wrapper and preview downloads
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        api = TraceMoe(token=os.getenv("TRACE_MOE_KEY"), client=client, max_retries=3)
        response = await api.search(args.source)

        best = response.best_result
        if best is None:
            raise SystemExit("No matches found")
        print(f"Best match: {best.filename} at {best.at}s ({best.short_similarity()})")

        stem = f"{best.anilist_id}_{int(best.anime_from)}"
        await asyncio.gather(
            download(client, best.image_url(size="l"), args.output / f"{stem}.jpg"),
            download(client, best.video_url(size="l", mute=True, max_duration=3), args.output / f"{stem}.mp4"),
        )


if __name__ == "__main__":
    asyncio.run(main())
