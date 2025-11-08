import asyncio
import logging
import os
from pyrogram import Client, idle
from aiohttp import web
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from Database.db import init_db
from downloader import L, login_instaloader, L

# --- File & Console Logging Setup ---
LOG_FILE = "bot_logs.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Bot Client Definition ---
app = Client(
    "InstaDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="Plugins")
)

# --- Web Server for Health Checks ---
async def health_check(request):
    """A simple health check endpoint."""
    return web.Response(text="Bot is alive and running!", status=200)

async def start_web_server():
    """Initializes and starts the lightweight web server."""
    web_app = web.Application()
    web_app.add_routes([web.get('/', health_check)])
    port = int(os.environ.get("PORT", 8080))
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    try:
        await site.start()
        logger.info(f"Web server started successfully on port {port}")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        raise
    return runner, site

# --- NEW: Background Task for Instaloader ---
async def background_instaloader_login():
    """
    Attempts to log into Instaloader in the background
    so it doesn't block bot startup.
    """
    logger.info("Starting background Instaloader login...")
    await asyncio.sleep(5) # Give the bot 5 seconds to start up
    try:
        # Run the blocking login function in a separate thread
        await asyncio.to_thread(login_instaloader)
        logger.info("Background Instaloader login attempt complete.")
    except Exception as e:
        logger.error(f"Background Instaloader login task failed: {e}")

# --- Main Bot & Server Function ---
async def main():
    """Main function to start the bot and web server."""
    await init_db()
    logger.info("Database initialized.")

    # --- START WEB AND BOT FIRST ---
    # This ensures the bot is responsive immediately
    web_runner, web_site = await start_web_server()

    logger.info("Starting Bot...")
    await app.start()
    
    logger.info("Bot is starting up...")

    # --- NOW, try the Instaloader login in the background ---
    # This is no longer blocking startup.
    asyncio.create_task(background_instaloader_login())

    try:
        me = await app.get_me()
        logger.info(f"Bot started as {me.first_name} (@{me.username})")
        
        # Send restart message to admin
        if ADMIN_ID != 0:
            try:
                await app.send_message(ADMIN_ID, "✅ **Bot has restarted successfully!**\n\nI'm online and ready.")
            except Exception as e:
                logger.warning(f"Could not send restart message to ADMIN_ID {ADMIN_ID}. Error: {e}")
        else:
            logger.warning("ADMIN_ID is not set. Skipping restart message.")

    except Exception as e:
        logger.error(f"Failed to get bot info or send restart message: {e}")

    # Keep the script running
    await idle()
    
    # --- Shutdown sequence ---
    # This code runs after /stop or Ctrl+C
    logger.info("Shutting down...")
    await web_runner.cleanup()  # Cleanly stop the web server
    logger.info("Web server stopped.")
    # We skip app.stop() as it can cause loop errors on Render
    # The OS will terminate the process.

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
