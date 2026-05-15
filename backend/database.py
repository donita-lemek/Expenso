"""
backend/database.py
In-memory dictionary database for Expenso.
Mocking the Database API for seamless local execution.
"""
import asyncio
import os
import sys

# In-memory storage
_STORAGE = {
    "claims": [],
    "employees": [],
    "policy": []
}

class MockCursor:
    def __init__(self, items):
        self.items = items
    
    async def to_list(self, length=None):
        return [dict(item) for item in self.items]

class MockCollection:
    def __init__(self, name):
        self.name = name

    def find(self, query=None):
        if not query:
            return MockCursor(_STORAGE[self.name])
        
        results = []
        for item in _STORAGE[self.name]:
            match = True
            for k, v in query.items():
                if isinstance(v, dict) and "$in" in v:
                    if item.get(k) not in v["$in"]:
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(item)
        return MockCursor(results)

    async def find_one(self, query):
        for item in _STORAGE[self.name]:
            match = True
            for k, v in query.items():
                if isinstance(v, dict) and "$in" in v:
                    if item.get(k) not in v["$in"]:
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                return dict(item)
        return None

    async def insert_one(self, doc):
        from copy import deepcopy
        _STORAGE[self.name].append(deepcopy(doc))
        class InsertResult:
            inserted_id = "mock_id"
        return InsertResult()

    async def insert_many(self, docs):
        from copy import deepcopy
        for doc in docs:
            _STORAGE[self.name].append(deepcopy(doc))

    async def update_one(self, query, update):
        for item in _STORAGE[self.name]:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                if "$set" in update:
                    item.update(update["$set"])
                return
                
    async def delete_one(self, query):
        for i, item in enumerate(_STORAGE[self.name]):
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                _STORAGE[self.name].pop(i)
                class DeleteResult:
                    deleted_count = 1
                return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()

    async def count_documents(self, query):
        cursor = self.find(query)
        res = await cursor.to_list()
        return len(res)

class MockDatabase:
    @property
    def claims(self): return MockCollection("claims")
    @property
    def employees(self): return MockCollection("employees")
    @property
    def policy(self): return MockCollection("policy")

class DatabaseManager:
    def __init__(self):
        self.db = MockDatabase()
        self._seeded = False

    async def connect(self):
        if not self._seeded:
            try:
                count = await self.db.claims.count_documents({})
                if count == 0:
                    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                    from seed import get_seed_data
                    seed_data = get_seed_data()
                    
                    print("🌱 In-Memory DB is empty. Seeding data...")
                    if seed_data.get("claims"):
                        await self.db.claims.insert_many(seed_data["claims"])
                    if seed_data.get("employees"):
                        await self.db.employees.insert_many(seed_data["employees"])
                    if seed_data.get("policy"):
                        await self.db.policy.insert_many(seed_data["policy"])
                        
                    print("🌱 In-Memory DB seeded successfully.")
                else:
                    print("🌿 In-Memory DB already seeded.")
            except Exception as e:
                print(f"⚠️ Seeding failed: {e}")
            self._seeded = True

    async def disconnect(self):
        print("🔌 In-Memory DB connection closed.")

db_instance = DatabaseManager()

async def connect_to_db():
    await db_instance.connect()

async def close_db_connection():
    await db_instance.disconnect()

async def get_database():
    return db_instance.db
