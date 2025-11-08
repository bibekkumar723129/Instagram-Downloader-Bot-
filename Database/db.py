import aiosqlite
import logging
from config import DB_NAME
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_FILE = DB_NAME

async def init_db():
    """Initializes the database and creates tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_premium BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                is_banned BOOLEAN DEFAULT FALSE,
                join_date TEXT NOT NULL,
                download_count INTEGER DEFAULT 0,
                last_download_date TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                stat_key TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        ''')
        # Initialize total downloads stat if not present
        await db.execute("INSERT OR IGNORE INTO stats (stat_key, value) VALUES ('total_downloads', 0)")
        await db.commit()
    logger.info("Database initialized successfully.")

async def add_user(user_id: int):
    """Adds a new user to the database or ignores if already exists."""
    join_date = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_FILE) as db:
        try:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)",
                (user_id, join_date)
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

async def get_user(user_id: int):
    """Retrieves a user's data from the database."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Return as a dictionary
                keys = [desc[0] for desc in cursor.description]
                return dict(zip(keys, row))
            return None

async def update_user_premium(user_id: int, is_premium: bool):
    """Updates a user's premium status."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("UPDATE users SET is_premium = ? WHERE user_id = ?", (is_premium, user_id))
        await db.commit()

async def update_user_ban(user_id: int, is_banned: bool):
    """Updates a user's banned status."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (is_banned, user_id))
        await db.commit()

async def update_user_admin(user_id: int, is_admin: bool):
    """Updates a user's admin status."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (is_admin, user_id))
        await db.commit()

async def get_all_user_ids():
    """Gets all user IDs for broadcasting."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_banned = FALSE") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_bot_stats():
    """Retrieves statistics for the admin panel."""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
        
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE") as cursor:
            premium_users = (await cursor.fetchone())[0]
        
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = TRUE") as cursor:
            banned_users = (await cursor.fetchone())[0]

        async with db.execute("SELECT value FROM stats WHERE stat_key = 'total_downloads'") as cursor:
            total_downloads_row = await cursor.fetchone()
            total_downloads = total_downloads_row[0] if total_downloads_row else 0
            
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "banned_users": banned_users,
            "total_downloads": total_downloads
        }

async def increment_download_count(user_id: int):
    """Increments a user's daily download count and total downloads."""
    today = datetime.utcnow().date().isoformat()
    async with aiosqlite.connect(DATABASE_FILE) as db:
        user = await get_user(user_id)
        current_count = user.get('download_count', 0)
        last_date = user.get('last_download_date')
        
        if last_date != today:
            current_count = 1
        else:
            current_count += 1
        
        await db.execute(
            "UPDATE users SET download_count = ?, last_download_date = ? WHERE user_id = ?",
            (current_count, today, user_id)
        )
        
        # Increment total bot downloads
        await db.execute("UPDATE stats SET value = value + 1 WHERE stat_key = 'total_downloads'")
        await db.commit()
        return current_count

async def get_daily_download_count(user_id: int):
    """Gets the user's download count for today."""
    today = datetime.utcnow().date().isoformat()
    user = await get_user(user_id)
    if not user:
        return 0
        
    last_date = user.get('last_download_date')
    if last_date != today:
        return 0 # Reset count for the new day
    
    return user.get('download_count', 0)
