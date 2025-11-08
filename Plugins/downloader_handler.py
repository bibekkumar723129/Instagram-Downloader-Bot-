import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from config import FREE_USER_DOWNLOAD_LIMIT
from Database.db import (
    get_user, add_user, increment_download_count, get_daily_download_count
)
from downloader import (
    INSTA_REGEX, download_media, cleanup_directory
)

logger = logging.getLogger(__name__)

# This regex finds all URLs in a message
URL_REGEX = r"https?:\/\/(www\.)?instagram\.com\/(?:p|reel|tv|stories|s)\/[a-zA-Z0-9_.-]+\/?"


@Client.on_message(filters.regex(INSTA_REGEX) & filters.private)
async def handle_insta_link(client: Client, message: Message):
    """Main handler for processing Instagram links."""
    user_id = message.from_user.id
    
    # 1. Check user in DB
    user = await get_user(user_id)
    if not user:
        await add_user(user_id)
        user = await get_user(user_id)
    
    # 2. Check if banned
    if user.get('is_banned', False):
        await message.reply_text("You are banned from using this bot.")
        return
        
    # 3. Check download limit for free users
    is_premium = user.get('is_premium', False)
    if not is_premium:
        daily_count = await get_daily_download_count(user_id)
        if daily_count >= FREE_USER_DOWNLOAD_LIMIT:
            await message.reply_text(
                f"You have reached your daily limit of {FREE_USER_DOWNLOAD_LIMIT} downloads.\n"
                "Please /upgrade for unlimited downloads."
            )
            return

    # Find all Instagram links in the message
    urls = re.findall(URL_REGEX, message.text)
    if not urls:
        # This should not happen if INSTA_REGEX matched, but as a safeguard.
        await message.reply_text("No valid Instagram links found.")
        return
        
    sent_msg = await message.reply_text(f"Found {len(urls)} link(s). Processing...")
    
    download_success_count = 0
    
    for i, url in enumerate(urls):
        url = url[0] if isinstance(url, tuple) else url # Ensure url is a string
        if not url.startswith("http"):
            url = "https://" + url

        await sent_msg.edit_text(f"Downloading link {i+1}/{len(urls)}...\n{url}")
        
        media_files, caption, target_dir, error = await download_media(url, user_id)
        
        if error:
            await message.reply_text(f"Failed to download {url}:\n`{error}`")
            await cleanup_directory(target_dir)
            continue
            
        # Send the media
        try:
            media_group = []
            final_caption = (caption or "") + "\n\nDownloaded via @YourBotUsername"

            for j, file_path in enumerate(media_files):
                # Add caption only to the first item in the group
                item_caption = final_caption if j == 0 else None
                
                if file_path.endswith(('.mp4', '.mov', '.avi')):
                    media_group.append(InputMediaVideo(file_path, caption=item_caption))
                elif file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    media_group.append(InputMediaPhoto(file_path, caption=item_caption))

            if media_group:
                if len(media_group) > 1:
                    await message.reply_media_group(media_group)
                else:
                    # Send as single file if not a group
                    if media_files[0].endswith(('.mp4', '.mov', '.avi')):
                         await message.reply_video(media_files[0], caption=final_caption)
                    else:
                         await message.reply_photo(media_files[0], caption=final_caption)
                
                download_success_count += 1
                
                # Increment download count if user is not premium
                if not is_premium:
                    await increment_download_count(user_id)
                    
            else:
                await message.reply_text(f"Download complete for {url}, but no media was found to send.")

        except Exception as e:
            logger.error(f"Failed to send media for {url}: {e}")
            await message.reply_text(f"Failed to send media for {url}.\n`{e}`")
        finally:
            # Clean up files
            await cleanup_directory(target_dir)

    # Final message
    try:
        if download_success_count > 0:
            await sent_msg.edit_text(f"Successfully downloaded and sent media for {download_success_count}/{len(urls)} link(s).")
            await asyncio.sleep(5)
            await sent_msg.delete()
        else:
            await sent_msg.edit_text("Finished processing. No media was successfully downloaded.")
    except Exception:
        pass # Message might be deleted already
