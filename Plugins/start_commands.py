from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from config import (
    START_TEXT, HELP_TEXT, ABOUT_TEXT, UPGRADE_TEXT, PREMIUM_QR_CODE, 
    FREE_USER_DOWNLOAD_LIMIT, ADMIN_ID
)
from Database.db import add_user, get_user, update_user_admin

# --- Keyboards ---

def get_main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Help", callback_data="help_cb"),
                InlineKeyboardButton("About", callback_data="about_cb")
            ],
            [
                InlineKeyboardButton("💎 Upgrade to Premium 💎", callback_data="upgrade_cb")
            ]
        ]
    )

def get_back_keyboard(back_to: str = "start_cb"):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Back", callback_data=back_to)]
        ]
    )

def get_upgrade_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Back", callback_data="start_cb")]
        ]
    )


# --- Handlers ---

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handler for the /start command."""
    user_id = message.from_user.id
    # Add user to DB
    await add_user(user_id)
    
    # Check if this is the first admin
    if user_id == ADMIN_ID:
        await update_user_admin(user_id, True)
    
    await message.reply_text(
        START_TEXT,
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Handler for the /help command."""
    await message.reply_text(
        HELP_TEXT.format(limit=FREE_USER_DOWNLOAD_LIMIT),
        reply_markup=get_back_keyboard("start_cb"),
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message: Message):
    """Handler for the /about command."""
    await message.reply_text(
        ABOUT_TEXT,
        reply_markup=get_back_keyboard("start_cb"),
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("upgrade") & filters.private)
async def upgrade_command(client: Client, message: Message):
    """Handler for the /upgrade command."""
    await message.reply_photo(
        photo=PREMIUM_QR_CODE,
        caption=UPGRADE_TEXT,
        reply_markup=get_upgrade_keyboard()
    )

# --- Callback Query Handlers ---

@Client.on_callback_query()
async def callback_query_handler(client: Client, query: CallbackQuery):
    """Main handler for all button presses."""
    data = query.data
    
    try:
        if data == "start_cb":
            await query.message.edit_text(
                START_TEXT,
                reply_markup=get_main_keyboard(),
                disable_web_page_preview=True
            )
        
        elif data == "help_cb":
            await query.message.edit_text(
                HELP_TEXT.format(limit=FREE_USER_DOWNLOAD_LIMIT),
                reply_markup=get_back_keyboard("start_cb"),
                disable_web_page_preview=True
            )
        
        elif data == "about_cb":
            await query.message.edit_text(
                ABOUT_TEXT,
                reply_markup=get_back_keyboard("start_cb"),
                disable_web_page_preview=True
            )
            
        elif data == "upgrade_cb":
            # Check if message is photo
            if query.message.photo:
                await query.message.edit_caption(
                    caption=UPGRADE_TEXT,
                    reply_markup=get_upgrade_keyboard()
                )
            else:
                # If not a photo, delete text message and send photo
                await query.message.delete()
                await query.message.reply_photo(
                    photo=PREMIUM_QR_CODE,
                    caption=UPGRADE_TEXT,
                    reply_markup=get_upgrade_keyboard()
                )
        
        else:
            await query.answer("Unknown button.", show_alert=True)
            
    except Exception as e:
        # Handle cases where the message is too old to edit, etc.
        logger.error(f"Callback query error: {e}")
        await query.answer("An error occurred.", show_alert=True)
