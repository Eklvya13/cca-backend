from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv
from bson.objectid import ObjectId
import os
from datetime import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

class DatabaseManager:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client["call_center_db"]
        self.fs = AsyncIOMotorGridFSBucket(self.db)

    async def add_employee(self, name, email, unique_employee_id):
        employee = {
            "name": name,
            "email": email,
            "unique_employee_id": unique_employee_id,
            "created_at": datetime.now()
        }
        if await self.db.employees.find_one({"unique_employee_id": unique_employee_id}):
            raise ValueError("Unique employee ID already exists")
        result = await self.db.employees.insert_one(employee)
        return str(result.inserted_id)

    async def get_employee(self, unique_employee_id):
        employee = await self.db.employees.find_one({"unique_employee_id": unique_employee_id})
        if employee:
            employee["_id"] = str(employee["_id"])
        return employee

    async def delete_employee(self, unique_employee_id):
        employee = await self.get_employee(unique_employee_id)
        if not employee:
            return False
        calls = await self.db.calls.find({"employee_id": employee["_id"]}).to_list(None)
        for call in calls:
            await self.db.analysis_results.delete_one({"call_id": str(call["_id"])})
            await self.fs.delete(ObjectId(call["file_id"]))
            await self.db.calls.delete_one({"_id": call["_id"]})
        await self.db.employees.delete_one({"unique_employee_id": unique_employee_id})
        return True

    async def edit_employee(self, unique_employee_id, name=None, email=None):
        employee = await self.get_employee(unique_employee_id)
        if not employee:
            return False
        update_data = {}
        if name: update_data["name"] = name
        if email: update_data["email"] = email
        if update_data:
            await self.db.employees.update_one(
                {"unique_employee_id": unique_employee_id},
                {"$set": update_data}
            )
        return True

    async def search_employee(self, unique_employee_id):
        return await self.get_employee(unique_employee_id)

    async def add_call(self, employee_unique_id, audio_file, duration):
        employee = await self.get_employee(employee_unique_id)
        if not employee:
            raise ValueError("Employee not found")
        # Auto-increment call_id
        last_call = await self.db.calls.find_one(sort=[("call_id", -1)])
        call_id = (last_call["call_id"] + 1) if last_call else 1
        # Store audio in GridFS (for analysis_results later)
        file_id = await self.fs.upload_from_stream(f"call_{call_id}.wav", audio_file)
        call = {
            "call_id": call_id,
            "employee_unique_id": employee_unique_id,
            "call_time": datetime.now(),
            "duration": duration,
            "numerical_score": None,
            "isAnalysed": False
        }
        if await self.db.calls.find_one({"call_id": call_id}):
            raise ValueError("Call ID already exists")
        result = await self.db.calls.insert_one(call)
        return {"call_id": call_id, "file_id": str(file_id)}  # Return file_id for analysis
    

    async def remove_call(self, call_id):
        call = await self.db.calls.find_one({"call_id": call_id})
        if not call:
            return False
        await self.db.analysis_results.delete_one({"call_id": call_id})
        # Note: Can't delete file_id here; it's in analysis_results (add later)
        await self.db.calls.delete_one({"call_id": call_id})
        return True

# Seed dummy data
async def seed_db():
    db = DatabaseManager()
    await db.add_employee("Alice Johnson", "alice@callcenter.com", 1001)
    await db.add_employee("Bob Carter", "bob@callcenter.com", 1002)
    await db.add_employee("Clara Lee", "clara@callcenter.com", 1003)
    await db.add_employee("David Kim", "david@callcenter.com", 1004)
    print("Seeded 4 employees")

# Test
async def test_db1():
    db = DatabaseManager()
    employee_id = await db.add_employee("Jane Smith", "jane@example.com", 1005)
    print(f"Added: {employee_id}")
    emp = await db.search_employee(1005)
    print(f"Searched: {emp}")
    await db.edit_employee(1005, name="Jane Doe")
    print(f"Edited: {await db.get_employee(1005)}")
    await db.delete_employee(1005)
    print(f"Deleted: {await db.get_employee(1005)}")

async def test_db():
    db = DatabaseManager()
    # Add call (use a dummy file stream)
    with open("test.wav", "rb") as audio_file:  # Create a test.wav locally
        result = await db.add_call(1006, audio_file, 300)
        print(f"Added call: {result}")
    call = await db.db.calls.find_one({"call_id": 1})
    print(f"Fetched call: {call}")
    # await db.remove_call(1)
    # print(f"Deleted call: {await db.db.calls.find_one({'call_id': 1})}")

if __name__ == "__main__":
    import asyncio
    #asyncio.run(seed_db())  # Run once, then comment out and use test_db()
    asyncio.run(test_db())