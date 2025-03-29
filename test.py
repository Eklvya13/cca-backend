# test.py
def add_analysis():
    import requests

    # Define API endpoint
    url = "http://127.0.0.1:8000/admin/call/1002"  # Replace 1001 with an existing employee ID

    # Open the audio file in binary mode
    with open("test.wav", "rb") as audio_file:
        files = {"audio_file": ("test.wav", audio_file, "audio/wav")}
        data = {"duration": "4500"}  # Form-data field for duration (in seconds)

        # Send the request
        response = requests.post(url, files=files, data=data)

    # Print the response
    print(response.json())


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

        
