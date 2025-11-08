import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import ADMIN_ID
from Database.db import (
    get_bot_stats, get_all_user_ids, update_user_premium, 
    update_user_ban, get_user, update_user_admin
)

logger = logging.getLogger(__name__)

# --- Admin Check Filter ---
admin_filter = filters.user(ADMIN_ID)

# --- Helper Function ---
async def get_user_id_from_message(message: Message) -> int | None:
    """Helper to get user_id from command args or reply."""
    user_id = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            user_id = int(args[1])
    return user_id

# --- Admin Commands ---

@Client.on_message(filters.command("stats") & admin_filter & filters.private)
async def stats_command(client: Client, message: Message):
    """Sends bot usage statistics."""
    stats = await get_bot_stats()
    await message.reply_text(
        f"**Bot Statistics**\n\n"
        f"Total Users: `{stats['total_users']}`\n"
        f"Premium Users: `{stats['premium_users']}`\n"
        f"Banned Users: `{stats['banned_users']}`\n"
        f"Total Downloads: `{stats['total_downloads']}`"
    )

@Client.on_message(filters.command("broadcast") & admin_filter & filters.private)
async def broadcast_command(client: Client, message: Message):
    """Broadcasts a message to all non-banned users."""
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to broadcast it.")
        return

    broadcast_msg = message.reply_to_message
    user_ids = await get_all_user_ids()
    
    sent_msg = await message.reply_text(f"Broadcasting to {len(user_ids)} users...")
    
    success_count = 0
    fail_count = 0
    
    for user_id in user_ids:
        try:
            await broadcast_msg.copy(chat_id=user_id)
            success_count += 1
        except FloodWait as e:
            logger.warning(f"FloodWait for {e.x} seconds. Pausing broadcast.")
            await asyncio.sleep(e.x)
            await broadcast_msg.copy(chat_id=user_id) # Retry
            success_count += 1
        except (UserIsBlocked, InputUserDeactivated):
            logger.info(f"User {user_id} blocked the bot. Skipping.")
            fail_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            fail_count += 1
        
        # Avoid hitting API limits
        if success_count % 100 == 0:
            await asyncio.sleep(1)
            
    await sent_msg.edit_text(
        f"**Broadcast Complete**\n\n"
        f"Sent to: `{success_count}` users\n"
        f"Failed for: `{fail_count}` users"
    )

@Client.on_message(filters.command("grant_premium") & admin_filter & filters.private)
async def grant_premium_command(client: Client, message: Message):
    """Grants premium access to a user."""
    user_id = await get_user_id_from_message(message)
    if not user_id:
        await message.reply_text("Reply to a user or provide user ID.")
        return
        
    user = await get_user(user_id)
    if not user:
        await message.reply_text("User not found in database.")
        return

    await update_user_premium(user_id, True)
    await message.reply_text(f"User `{user_id}` has been granted premium access.")
    # Notify the user
    try:
        await client.send_message(user_id, "Congratulations! You are now a Premium user. 💎")
    except Exception:
        pass # User might have blocked the bot

@Client.on_message(filters.command("revoke_premium") & admin_filter & filters.private)
async def revoke_premium_command(client: Client, message: Message):
    """Revokes premium access from a user."""
    user_id = await get_user_id_from_message(message)
    if not user_id:
        await message.reply_text("Reply to a user or provide user ID.")
        return
        
    user = await get_user(user_id)
    if not user:
        await message.reply_text("User not found in database.")
        return

    await update_user_premium(user_id, False)
    await message.reply_text(f"Premium access for user `{user_id}` has been revoked.")
    try:
        await client.send_message(user_id, "Your premium access has been revoked by an admin.")
    except Exception:
        pass

@Client.on_message(filters.command("ban") & admin_filter & filters.private)
async def ban_command(client: Client, message: Message):
    """Bans a user from using the bot."""
    user_id = await get_user_id_from_message(message)
    if not user_id:
        await message.reply_text("Reply to a user or provide user ID.")
        return
        
    if user_id == ADMIN_ID:
        await message.reply_text("You cannot ban yourself, admin.")
        return
        
    await update_user_ban(user_id, True)
    await message.reply_text(f"User `{user_id}` has been banned.")

@Client.on_message(filters.command("unban") & admin_filter & filters.private)
async def unban_command(client: Client, message: Message):
    """Unbans a user."""
    user_id = await get_user_id_from_message(message)
    if not user_id:
        await message.reply_text("Reply to a user or provide user ID.")
        return
        
    await update_user_ban(user_id, False)
    await message.reply_text(f"User `{user_id}` has been unbanned.")

@Client.on_message(filters.command("add_admin") & admin_filter & filters.private)
async def add_admin_command(client: Client, message: Message):
    """Grants admin access to a user."""
    user_id = await get_user_id_from_message(message)
    if not user_id:
        await message.reply_text("Reply to a user or provide user ID.")
        return
    await update_user_admin(user_id, True)
    await message.reply_text(f"User `{user_id}` is now an admin.")
