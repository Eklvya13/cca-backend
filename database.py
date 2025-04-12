from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from google.cloud import storage
import os
from datetime import datetime, timedelta
import asyncio
from utils import convert_to_mono

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GCS_CRED_NAME")

class GCSHandler:
    def __init__(self, bucket_name="cca-backend-calls"):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    async def upload_audio(self, file_path, filename):
        blob = self.bucket.blob(filename)
        with open(file_path, "rb") as file:
            blob.upload_from_file(file, content_type="audio/wav")
        return filename

    async def generate_signed_url(self, filename, expiration_minutes=60):
        blob = self.bucket.blob(filename)
        url = blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))
        return url

    async def delete_audio(self, filename):
        blob = self.bucket.blob(filename)
        blob.delete()
        return True

# Initialize GCS handler
gcs = GCSHandler()

class DatabaseManager:
    def __init__(self):
        loop = asyncio.get_event_loop()
        self.client = AsyncIOMotorClient(MONGO_URI, io_loop=loop)
        self.db = self.client["call_center_db"]

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

    #calls collection methods here
    async def add_call(self, employee_unique_id, duration, audio_file):
        """Uploads an audio file to GCS and stores metadata in MongoDB."""
        employee = await self.db.employees.find_one({"unique_employee_id": employee_unique_id})
        if not employee:
            raise ValueError("Employee not found")

        last_call = await self.db.calls.find_one(sort=[("call_id", -1)])
        call_id = (last_call["call_id"] + 1) if last_call else 1

        call_id_str = f"{call_id:03}"

        # Convert audio to mono and save it
        audio_file = convert_to_mono(audio_file)
        audio_file.seek(0)  # Reset file pointer to the beginning
        with open(f"./assets/recordings/{call_id_str}.wav", "wb") as f:
            f.write(audio_file.read())

        # Format call_id as a zero-padded 3-digit string for ex 001, 012 etc
        filepath = f"./assets/recordings/{call_id_str}.wav"
        filename = f"calls/{employee_unique_id}_{call_id_str}.wav"

        try:
            await gcs.upload_audio(file_path=filepath, filename=filename)
        except Exception as e:
            raise RuntimeError(f"GCS upload failed: {str(e)}")

        call = {
            "call_id": call_id,
            "employee_unique_id": employee_unique_id,
            "call_time": datetime.now(),
            "duration": duration,
            "numerical_score": None,
            "isAnalysed": False,
            "audio_filename": filename
        }
        result = await self.db.calls.insert_one(call)
        return call_id, filename

    async def get_audio_url(self, call_id):
        """Generates a signed URL for secure audio access."""
        call = await self.db.calls.find_one({"call_id": call_id})
        if not call or "audio_filename" not in call:
            return None
        return await gcs.generate_signed_url(call["audio_filename"])
    
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
        if not call_data or "audio_filename" not in call_data:
            raise ValueError("audio filename not found for this call")

        callname = call_data['audio_filename']

        analysis = {
            "call_id": call_id,
            "scorecard_a": scorecard_a,
            "scorecard_b": scorecard_b,
            "final_score": final_score,
            "transcript": "",
            "audio_filename": callname
        }
        result = await self.db.analysis_results.insert_one(analysis)
        return str(result.inserted_id)

    async def get_analysis(self, call_id):
        analysis = await self.db.analysis_results.find_one({"call_id": call_id})
        if analysis:
            analysis["_id"] = str(analysis["_id"])
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
    
    async def get_employee_summary(self, employee_id: str):
        calls_cursor = self.db.calls.find({"employee_unique_id": int(employee_id)})
        calls = await calls_cursor.to_list(length=None)

        if not calls:
            return None

        total_calls = len(calls)
        durations = [call.get("duration", 0) for call in calls]
        scores = [call.get("numerical_score", 0) or 0 for call in calls]

        avg_duration = round(sum(durations) / total_calls, 2)
        avg_score = round(sum(scores) / total_calls, 2)

        def simulate_emotion(score):
            if score >= 75:
                return "positive"
            elif score >= 50:
                return "neutral"
            return "negative"

        emotion_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for score in scores:
            mood = simulate_emotion(score)
            emotion_counts[mood] += 1

        emotion_distribution = {
            k: round((v / total_calls) * 100, 2) for k, v in emotion_counts.items()
        }

        calls_list = [
            {
                "call_id": call["call_id"],
                "employee_id": call["employee_unique_id"],
                "call_duration": call.get("duration", 0),
                "numerical_score": call.get("numerical_score", 0),
                "is_analyzed": call.get("isAnalysed", False),
                "audio_filename": call.get("audio_filename", "")
            }
            for call in calls
        ]

        return {
            "employee_id": employee_id,
            "total_calls": total_calls,
            "average_duration": avg_duration,
            "average_score": avg_score,
            "emotion_distribution": emotion_distribution,
            "calls": calls_list
        }

    async def delete_analysis(self, call_id):
        """Deletes an analysis entry and associated GCS file."""
        analysis = await self.db.analysis_results.find_one({"call_id": call_id})
        if not analysis:
            return False

        call = await self.db.calls.find_one({"call_id": call_id})
        if call and "audio_filename" in call:
            await gcs.delete_audio(call["audio_filename"])  # Delete file from GCS

        await self.db.analysis_results.delete_one({"call_id": call_id})
        return True


_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance

async def test_db1():
    db = DatabaseManager()
    employee_id = await db.add_employee("Jane Smith", "jane@example.com", 1005)
    print(f"Added: {employee_id}")
    emp = await db.search_employee(1005)
    print(f"Searched: {emp}")
    await db.edit_employee(1005, name="Jane Doe")
    print(f"Edited: {await db.get_employee(1005)}")

if __name__ == "__main__":
    import asyncio
    #asyncio.run(seed_db())  # Run once, then comment out and use test_db()
    asyncio.run(test_db1())