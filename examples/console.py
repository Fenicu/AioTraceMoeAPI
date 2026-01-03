import asyncio
import datetime as dt

from aiotracemoeapi import TraceMoe, exceptions, types


async def main():
    """
    Demonstrate a simple search by URL using the aiotracemoeapi library.
    """
    api = TraceMoe()
    
    # URL of the image to search
    # Using a known anime screenshot
    image_url = "https://s1.zerochan.net/Kurosaki.Ichigo.600.172225.jpg"
    
    print(f"Searching for image: {image_url}")

    try:
        # Perform the search
        # is_url=True is required when passing a URL string
        response = await api.search(image_url, is_url=True)
        
        print(f"Search completed. Found {len(response.result)} results.")

        if response.result:
            best = response.best_result
            print("\n--- Best Match ---")
            print(f"Similarity: {best.short_similarity()}")
            
            # The 'anilist' field can be an ID (int) or an AniList object depending on 'anilist_info' param (default True)
            if isinstance(best.anilist, types.AniList):
                english_title = best.anilist.title.get('english')
                romaji_title = best.anilist.title.get('romaji')
                title = english_title or romaji_title or "Unknown Title"
                print(f"Title: {title}")
                print(f"Is Adult: {'Yes' if best.anilist.is_adult else 'No'}")
                print(f"MAL URL: {best.anilist.mal_url}")
            else:
                print(f"AniList ID: {best.anilist}")
            
            # Episode can be a single value or a list
            episode = best.episode
            if isinstance(episode, list):
                episode = ", ".join(map(str, episode))
            print(f"Episode: {episode}")
            
            # Time in the episode
            start_time = dt.timedelta(seconds=int(best.anime_from))
            end_time = dt.timedelta(seconds=int(best.anime_to))
            print(f"Timestamp: {start_time} - {end_time}")
            
            print(f"Video Preview: {best.video}")
            
        else:
            print("No matches found.")

    except exceptions.SearchQueueFull:
        print("Error: Search queue is full, please try again later.")
    except exceptions.SearchQuotaDepleted:
        print("Error: Monthly search limit reached.")
    except exceptions.TraceMoeAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
