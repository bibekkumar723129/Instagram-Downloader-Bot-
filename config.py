import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Pyrogram Bot Config ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# --- Admin Config ---
# Add your user ID as ADMIN_ID
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0)) 

# --- Database Config ---
DB_NAME = os.environ.get("DB_NAME", "bot_database.db")

# --- Instagram Config ---
# !! WARNING !!
# Using an Instagram account for scraping is against their Terms of Service
# and can get the account BANNED. Use a burner/test account.
IG_USER = os.environ.get("IG_USER", "")
IG_PASS = os.environ.get("IG_PASS", "")

# --- Bot Settings ---
PREMIUM_QR_CODE = "https://i.ibb.co/hFjZ6CWD/photo-2025-08-10-02-24-51-7536777335068950548.jpg"
FREE_USER_DOWNLOAD_LIMIT = 5 # Downloads per day
PREMIUM_PRICE = "5$" # Example price

# --- Bot Text & Messages ---
START_TEXT = """
🚀 **Fastest Instagram Downloader Bot**
🎬 Download Reels • Posts • Stories • Highlights
💎 Unlock HD & Unlimited downloads with Premium!
📥 Just send any Instagram link below.
"""

HELP_TEXT = """
**How to use me:**

1.  Send me any public Instagram link:
    -   `.../p/post_code/`
    -   `.../reel/reel_code/`
    -   `.../tv/igtv_code/`
    -   `.../s/story_highlight_code/` (Highlights)
    -   `.../stories/username/story_id/` (Stories)

2.  You can send multiple links in one message.
3.  I will automatically detect them and send you the media.

**Free Users:**
-   You have a limit of {limit} downloads per day.

**Premium Users:**
-   Unlimited downloads.
-   Faster queue priority.
-   Ad-free experience.

Press /upgrade to see premium options.
"""

ABOUT_TEXT = """
**About This Bot**

This is a high-speed, lightweight Instagram Downloader Bot.

-   **Powered by:** [Python](https://www.python.org/) & [Pyrogram](https://pyrogram.org/)
-   **Downloader:** [Instaloader](https://instaloader.github.io/)
-   **Developer:** Your Name/Handle

This bot is provided for personal and educational use. Please respect copyright and Instagram's Terms of Service.
"""

UPGRADE_TEXT = f"""
**Unlock Premium Features!**

For just **{PREMIUM_PRICE}**, you get:
-   ✅ Unlimited Downloads
-   ✅ Highest HD Quality
-   ✅ Faster Download Queue
-   ✅ Ad-Free Experience

**How to Upgrade:**
1.  Make a payment to our portal (example QR code below).
2.  Contact an admin with your payment proof.

An admin will grant you premium access manually.
"""
