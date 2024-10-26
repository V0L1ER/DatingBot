import aiosqlite
import os

async def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = await aiosqlite.connect(db_path) 
    return conn