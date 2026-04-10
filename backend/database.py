"""
backend/database.py
MongoDB database for Expenso.
Automatically seeds on startup if collections are empty.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class MongoDBManager:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client.get_database("expenso_app")
        self._seeded = False

    async def connect(self):
        if not self._seeded:
            try:
                count = await self.db.claims.count_documents({})
                if count == 0:
                    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                    from seed import get_seed_data
                    seed_data = get_seed_data()
                    
                    print("🌱 MongoDB is empty. Seeding database...")
                    if seed_data.get("claims"):
                        await self.db.claims.insert_many(seed_data["claims"])
                    if seed_data.get("employees"):
                        await self.db.employees.insert_many(seed_data["employees"])
                    if seed_data.get("policy"):
                        await self.db.policy.insert_many(seed_data["policy"])
                        
                    print("🌱 MongoDB database seeded successfully.")
                else:
                    print("🌿 MongoDB already seeded.")
            except Exception as e:
                print(f"⚠️ MongoDB connection/seeding failed: {e}")
            self._seeded = True

    async def disconnect(self):
        self.client.close()
        print("🔌 MongoDB database connection closed.")

db_instance = MongoDBManager()

async def connect_to_mongo():
    await db_instance.connect()

async def close_mongo_connection():
    await db_instance.disconnect()

async def get_database():
    return db_instance.db
