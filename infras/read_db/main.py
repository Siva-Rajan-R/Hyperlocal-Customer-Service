from motor.motor_asyncio import AsyncIOMotorClient
from core.settings import CustomerSettings

READ_DB_URL="mongodb://localhost:27017"

CLIENT=None
READ_DATABASE=None

async def init_read_db():
    global CLIENT,READ_DATABASE
    CLIENT=AsyncIOMotorClient(READ_DB_URL)
    READ_DATABASE=CLIENT['CustomerReadDb']

async def close_read_db():
    global CLIENT
    if CLIENT:
        CLIENT.close()