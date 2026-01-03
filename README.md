# AioTraceMoeAPI

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/13726d8a3e134ee6bd6adf1bf66d6c8a)](https://app.codacy.com/gh/Fenicu/AioTraceMoeAPI?utm_source=github.com&utm_medium=referral&utm_content=Fenicu/AioTraceMoeAPI&utm_campaign=Badge_Grade_Settings)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![MIT License](https://img.shields.io/pypi/l/aiotracemoeapi)](https://opensource.org/licenses/MIT)
[![PyPi Package Version](https://img.shields.io/pypi/v/aiotracemoeapi)](https://pypi.python.org/pypi/aiotracemoeapi)
[![Downloads](https://img.shields.io/pypi/dm/aiotracemoeapi.svg)](https://pypi.python.org/pypi/aiotracemoeapi)
[![Supported python versions](https://img.shields.io/pypi/pyversions/aiotracemoeapi)](https://pypi.python.org/pypi/aiotracemoeapi)

A simple, but extensible asynchronous Python wrapper for the [trace.moe](https://trace.moe) API.

## Key Features

*   **Async**: Built on top of `httpx` for high-performance asynchronous HTTP requests.
*   **Typed**: Fully typed codebase for better developer experience and IDE support.
*   **Pydantic v2**: Uses Pydantic v2 for robust data validation and serialization.

## Installation

You can install the package using `uv` or `pip`:

```bash
uv add aiotracemoeapi
```

or

```bash
pip install aiotracemoeapi
```

## Usage Examples

### Basic Search by URL

```python
import asyncio
from aiotracemoeapi import TraceMoe

async def main():
    api = TraceMoe()
    
    # Search by URL
    # Note: is_url=True is required when passing a URL string
    result = await api.search("https://images.plurk.com/32B15UXxymfSMwKGTObY5e.jpg", is_url=True)
    
    if result.result:
        print(f"Anime: {result.result[0].filename}")
        print(f"Similarity: {result.result[0].similarity}")
    else:
        print("No results found.")

if __name__ == "__main__":
    asyncio.run(main())
```

### Search by File Upload

You can search using a local file path.

```python
import asyncio
from aiotracemoeapi import TraceMoe

async def main():
    api = TraceMoe()
    
    # Search by local file path
    # Ensure 'image.jpg' exists in your directory
    try:
        result = await api.search("image.jpg")
        
        if result.result:
            print(f"Anime: {result.result[0].filename}")
            print(f"Episode: {result.result[0].episode}")
    except FileNotFoundError:
        print("File not found!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Checking Account Status

You can check your API usage limits and quota.

```python
import asyncio
from aiotracemoeapi import TraceMoe

async def main():
    # Initialize with your API token (optional, but recommended for higher limits)
    # Get your token from https://trace.moe/account
    api = TraceMoe(token="your_token_here")
    
    me = await api.me()
    
    print(f"ID: {me.id}")
    print(f"Priority: {me.priority}")
    print(f"Quota Used: {me.quota_used}")
    print(f"Quota Total: {me.quota}")

if __name__ == "__main__":
    asyncio.run(main())
```
