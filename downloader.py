import instaloader
import asyncio
import os
import glob
import shutil
import logging
from config import IG_USER, IG_PASS
from instaloader.exceptions import *

logger = logging.getLogger(__name__)

# --- Instaloader Setup ---
L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern=None, # Disable caption .txt files
    storyitem_metadata_txt_pattern=None
)

def login_instaloader():
    """Logs into Instaloader. This is a blocking function."""
    if not IG_USER or not IG_PASS:
        logger.warning("No IG_USER or IG_PASS set. Running without login.")
        logger.warning("May face rate limits or fail to download stories/highlights.")
        return
    
    try:
        logger.info(f"Attempting Instaloader login as {IG_USER}...")
        L.login(IG_USER, IG_PASS)
        logger.info(f"Instaloader login successful for {IG_USER}.")
    except Exception as e:
        logger.error(f"Instaloader login failed for {IG_USER}: {e}")
        logger.warning("Continuing without login.")

# --- Regex for URL detection ---
POST_REGEX = r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)\/?"
STORY_REGEX = r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/stories\/([a-zA-Z0-9_.-]+)\/(\d+)\/?"
HIGHLIGHT_REGEX = r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/s\/([a-zA-Z0-9_-]+)\/?"
# Combined regex for all types
INSTA_REGEX = r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv|stories|s)\/.*"


async def download_media(url: str, user_id: int):
    """
    Downloads media from a given Instagram URL.
    Returns: (list_of_media_paths, caption, target_directory, error_message)
    """
    target_dir = f"downloads/{user_id}_{instaloader.utils.md5(url)}"
    
    try:
        if "/p/" in url or "/reel/" in url or "/tv/" in url:
            # It's a Post, Reel, or IGTV
            shortcode = url.split("/")[-2]
            post = await asyncio.to_thread(
                instaloader.Post.from_shortcode, L.context, shortcode
            )
            await asyncio.to_thread(L.download_post, post, target=target_dir)
            caption = post.caption
            
        elif "/stories/" in url:
            # It's a Story
            parts = url.split('/')
            username = parts[-3]
            story_id = int(parts[-2])
            
            profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
            story_item = None
            for item in await asyncio.to_thread(L.get_stories, [profile.userid]):
                if item.mediaid == story_id:
                    story_item = item
                    break
            
            if story_item:
                await asyncio.to_thread(L.download_storyitem, story_item, target=target_dir)
                caption = f"Story from {username}"
            else:
                return None, None, None, "Error: Story not found or expired."

        elif "/s/" in url:
            # It's a Highlight
            highlight_url = url.split('?')[0]
            
            # This is a bit of a hack as Instaloader doesn't have a direct
            # `from_url` for highlights. We try to get the owner.
            logger.warning("Highlight download is experimental.")
            # We can't easily get highlight items from just the URL.
            # This part is complex and often requires a logged-in session.
            # For this example, we'll state it's difficult.
            # A more robust solution would be needed.
            return None, None, None, "Error: Highlight downloads are complex and not fully supported in this version."

        else:
            return None, None, None, "Error: Unknown Instagram URL format."

        # Find all downloaded media files
        files = glob.glob(os.path.join(target_dir, "*.*"))
        # Filter out metadata files
        media_files = [f for f in files if not f.endswith(('.json', '.txt', '.xz'))]

        if not media_files:
            return None, None, target_dir, "Error: Downloaded, but no media files found."

        return media_files, (caption or ""), target_dir, None

    except ProfileNotExistsException:
        return None, None, target_dir, "Error: The profile does not exist."
    except PrivateProfileNotFollowedException:
        return None, None, target_dir, "Error: This is a private profile. The bot cannot access it."
    except LoginRequiredException:
        return None, None, target_dir, "Error: Login is required to view this. (Bot login may have failed)"
    except BadRequestsException:
        return None, None, target_dir, "Error: Bad request. The link might be invalid."
    except TooManyRequestsException:
        return None, None, target_dir, "Error: Bot is rate-limited by Instagram. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected download error for {url}: {e}")
        return None, None, target_dir, f"An unexpected error occurred: {e}"
    
async def cleanup_directory(directory: str):
    """Asynchronously removes a directory and its contents."""
    if directory and os.path.exists(directory):
        try:
            await asyncio.to_thread(shutil.rmtree, directory)
        except Exception as e:
            logger.error(f"Failed to clean up directory {directory}: {e}")
