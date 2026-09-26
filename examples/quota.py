"""
Show your search quota, limits and usage history.

    uv run examples/quota.py
    uv run examples/quota.py --period day

Set the TRACE_MOE_KEY environment variable to see your account instead of your IP address.
"""

import argparse
import asyncio
import os

from aiotracemoeapi import TraceMoe


async def main() -> None:
    parser = argparse.ArgumentParser(description="Show trace.moe quota and usage")
    parser.add_argument("--period", choices=["minute", "hour", "day"], default="hour")
    args = parser.parse_args()

    async with TraceMoe(token=os.getenv("TRACE_MOE_KEY")) as api:
        me = await api.me()
        usage = await api.usage(args.period)

    print(f"Account:     {me.id}")
    print(f"Priority:    {me.priority}")
    print(f"Concurrency: {me.concurrency} parallel searches")
    print(f"Quota:       {me.quota_used}/{me.quota} used in the last 24 hours, {me.quota_left} left")
    if me.limits:
        print(f"HTTP limit:  {me.limits.remaining}/{me.limits.limit} requests left this minute")

    print(f"\nUsage by {args.period}:")
    for slot in usage:
        if not slot.total:
            continue
        failed = {code: count for code, count in sorted(slot.by_status.items()) if code != 200 and count}
        line = f"  {slot.time:%Y-%m-%d %H:%M}  {slot.total:>4} searches"
        if failed:
            line += "  (errors: " + ", ".join(f"{code}: {count}" for code, count in failed.items()) + ")"
        print(line)


if __name__ == "__main__":
    asyncio.run(main())
