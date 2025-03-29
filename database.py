from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv
from bson.objectid import ObjectId
import os
from datetime import datetime
import asyncio

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

class DatabaseManager:
    def __init__(self):
        loop = asyncio.get_event_loop()
        self.client = AsyncIOMotorClient(MONGO_URI, io_loop=loop)
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

    #calls collection methods here
    async def add_call(self, employee_unique_id, duration, audio_file):
        employee = await self.get_employee(employee_unique_id)
        if not employee:
            raise ValueError("Employee not found")

        last_call = await self.db.calls.find_one(sort=[("call_id", -1)])
        call_id = (last_call["call_id"] + 1) if last_call else 1

        # Upload audio file and get file_id
        file_id = await self.upload_audio(call_id, audio_file)

        call = {
            "call_id": call_id,
            "employee_unique_id": employee_unique_id,
            "call_time": datetime.now(),
            "duration": duration,
            "numerical_score": None,
            "isAnalysed": False,
            "file_id": file_id  # Store file_id in calls collection
        }
        result = await self.db.calls.insert_one(call)
        return call_id, file_id  # Return both call_id and file_id

    
    async def remove_call(self, call_id):
        call = await self.get_call(call_id)
        if not call:
            return False
        await self.delete_analysis(call_id)  # Cascade to analysis and file
        await self.db.calls.delete_one({"call_id": call_id})
        return True
        
    async def get_call(self, call_id):
        call = await self.db.calls.find_one({"call_id": call_id})
        if call:
            call["_id"] = str(call["_id"])
        return call

    async def update_call_analysis(self, call_id, numerical_score):
        call = await self.get_call(call_id)
        if not call:
            return False
        await self.db.calls.update_one(
            {"call_id": call_id},
            {"$set": {"numerical_score": numerical_score, "isAnalysed": True}}
        )
        return True

    async def get_calls_by_employee(self, employee_unique_id):
        calls = await self.db.calls.find({"employee_unique_id": employee_unique_id}).to_list(None)
        for call in calls:
            call["_id"] = str(call["_id"])
        return calls

    #Here Lies the analysis results collection methods
    async def add_analysis(self, call_id, scorecard_a, scorecard_b, final_score):
        # Fetch file_id from calls collection
        call_data = await self.db.calls.find_one({"call_id": call_id})
        if not call_data or "file_id" not in call_data:
            raise ValueError("File ID not found for this call")

        file_id = call_data["file_id"]

        analysis = {
            "call_id": call_id,
            "scorecard_a": scorecard_a,
            "scorecard_b": scorecard_b,
            "final_score": final_score,
            "transcript": "",
            "file_id": file_id  # Use the file_id from the calls collection
        }
        result = await self.db.analysis_results.insert_one(analysis)
        return str(result.inserted_id)


    async def get_analysis(self, call_id):
        analysis = await self.db.analysis_results.find_one({"call_id": call_id})
        if analysis:
            analysis["_id"] = str(analysis["_id"])
            analysis["file_id"] = str(analysis["file_id"])
        return analysis

    async def update_analysis(self, call_id, scorecard_a=None, scorecard_b=None, final_score=None, transcript=None):
        analysis = await self.get_analysis(call_id)
        if not analysis:
            return False
        update_data = {}
        if scorecard_a is not None: update_data["scorecard_a"] = scorecard_a
        if scorecard_b is not None: update_data["scorecard_b"] = scorecard_b
        if final_score is not None: update_data["final_score"] = final_score
        if transcript is not None: update_data["transcript"] = transcript
        if update_data:
            await self.db.analysis_results.update_one(
                {"call_id": call_id},
                {"$set": update_data}
            )
        return True

    async def delete_analysis(self, call_id):
        analysis = await self.get_analysis(call_id)
        if not analysis:
            return False
        await self.fs.delete(ObjectId(analysis["file_id"]))
        await self.db.analysis_results.delete_one({"call_id": call_id})
        return True


    #Audio
    async def upload_audio(self, call_id, audio_file):
        file_id = await self.fs.upload_from_stream(f"call_{call_id}.wav", audio_file)
        return str(file_id)

    async def get_audio(self, call_id):
        analysis = await self.get_analysis(call_id)
        if not analysis or not analysis["file_id"]:
            return None
        return await self.fs.open_download_stream(ObjectId(analysis["file_id"]))

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

async def test_add_data():
    db = DatabaseManager()
    # Add employees
    emp1_id = await db.add_employee("Alice", "alice@example.com", 1001)
    emp2_id = await db.add_employee("Bob", "bob@example.com", 1002)
    print(f"Added employees: {emp1_id}, {emp2_id}")
    # Add calls
    call1_id = await db.add_call(1001, 300)
    call2_id = await db.add_call(1001, 450)
    print(f"Added calls: {call1_id}, {call2_id}")
    # Add analysis with dummy audio
    with open("test.wav", "rb") as audio_file:  # Need a test.wav file
        file_id = await db.upload_audio(call1_id, audio_file)
        analysis_id = await db.add_analysis(
            call1_id,
            {"accuracy": 8.5},  # scorecard_a
            {"emotion_score": 7.0},  # scorecard_b
            {"numeric": 7.5},  # final_score
            file_id
        )
        print(f"Added analysis: {analysis_id}, file_id: {file_id}")

async def test_update_data():
    db = DatabaseManager()
    # Update employee
    await db.edit_employee(1001, name="Alice Updated")
    print(f"Updated employee 1001")
    # Update call analysis
    await db.update_call_analysis(1, 8.0)
    print(f"Updated call 1 analysis")
    # Update analysis
    await db.update_analysis(1, transcript="Hello, this is a test.")
    print(f"Updated analysis for call 1")

async def test_upload_data():
    db = DatabaseManager()
    # Add new call
    call3_id = await db.add_call(1002, 600)
    print(f"Added call: {call3_id}")
    # Upload audio and analysis
    with open("test.wav", "rb") as audio_file:  # Need a test2.wav
        file_id = await db.upload_audio(call3_id, audio_file)
        analysis_id = await db.add_analysis(
            call3_id,
            {"speed": 9.0},
            {"calmness": 6.5},
            {"numeric": 7.8},
            file_id
        )
        print(f"Added analysis: {analysis_id}, file_id: {file_id}")

async def test_download_files():
    db = DatabaseManager()
    # Download call_1.wav
    stream1 = await db.get_audio(1)
    if stream1:
        with open("call_1.wav", "wb") as f:
            f.write(await stream1.read())
        print("Downloaded call_1.wav")
    else:
        print("call_1.wav not found")
    # Download call_2.wav
    stream2 = await db.get_audio(3)
    if stream2:
        with open("call_3.wav", "wb") as f:
            f.write(await stream2.read())
        print("Downloaded call_2.wav")
    else:
        print("call_2.wav not found")

async def test_delete_specific():
    db = DatabaseManager()
    # Delete call 2
    success = await db.remove_call(2)
    print(f"Deleted call 2: {success}")
    # Delete analysis for call 1
    success = await db.delete_analysis(1)
    print(f"Deleted analysis for call 1: {success}")

async def test_clear_db():
    db = DatabaseManager()
    await db.db.employees.drop()
    await db.db.calls.drop()
    await db.db.analysis_results.drop()
    await db.db["fs.files"].drop()
    await db.db["fs.chunks"].drop()
    print("Cleared all collections")

    
if __name__ == "__main__":
    import asyncio
    #asyncio.run(seed_db())  # Run once, then comment out and use test_db()
    asyncio.run(test_clear_db())