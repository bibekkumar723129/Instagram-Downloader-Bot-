import asyncio
import logging
from pyrogram import Client, idle
from config import API_ID, API_HASH, BOT_TOKEN
from Database.db import init_db
from downloader import L, login_instaloader

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the bot app
app = Client(
    "InstaDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="Plugins")
)

async def main():
    """Main function to start the bot."""
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Logging into Instaloader...")
    # Run Instaloader login in a separate thread
    await asyncio.to_thread(login_instaloader)
    
    logger.info("Starting Bot...")
    await app.start()
    
    try:
        me = await app.get_me()
        logger.info(f"Bot started as {me.first_name} (@{me.username})")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")

    await idle()
    
    logger.info("Stopping Bot...")
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
