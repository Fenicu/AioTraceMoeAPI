# Examples

Run any example from the repository root with `uv run`. Set `TRACE_MOE_KEY` to use your API key
(get it at https://trace.moe/account); without it you search as a guest by IP address.

| Example | What it shows |
| --- | --- |
| [`console.py`](console.py) | Command-line search by URL or file, `CutBorders`, AniList filter, error handling and retries |
| [`quota.py`](quota.py) | Quota, limits and usage history with `me()` and `usage()` |
| [`batch_folder.py`](batch_folder.py) | Searching a whole folder in parallel within your concurrency limit, saving a CSV |
| [`vector_search.py`](vector_search.py) | Single and batch search by ColorLayout vectors |
| [`download_preview.py`](download_preview.py) | Downloading preview images and clips, sharing your own `httpx.AsyncClient` |
| [`telegram_bot.py`](telegram_bot.py) | Telegram bot on aiogram 3 that replies to screenshots with the anime and a preview clip |

```bash
uv run examples/console.py https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg
uv run examples/console.py screenshot.jpg --cut-borders both --top 3
uv run examples/quota.py --period day
uv run examples/batch_folder.py ./screenshots results.csv
uv run examples/vector_search.py gwebWzth7oPe2UIubOJmozi1NDFp
uv run examples/download_preview.py screenshot.jpg --output ./previews
BOT_TOKEN=123:abc uv run examples/telegram_bot.py
```

`telegram_bot.py` declares its dependencies inline ([PEP 723](https://peps.python.org/pep-0723/)),
so `uv run` installs aiogram and the published aiotracemoeapi for it automatically.
