from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import HTMLResponse, FileResponse    
from database import DatabaseManager

app = FastAPI()
db = DatabaseManager()

# Temporary Home Page
@app.get("/welcome-temp", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Call Audio Player</title>
</head>
<body>

    <h2>Call Audio Player</h2>

    <label for="callId">Enter Call ID:</label>
    <input type="number" id="callId" placeholder="Enter Call ID" value="1">
    <button onclick="fetchAudio()">Get Audio</button>

    <br><br>
    <audio id="audioPlayer" controls style="display: none;">
        Your browser does not support the audio element.
    </audio>

    <script>
        function fetchAudio() {
            let callId = document.getElementById("callId").value;
            let url = `http://127.0.0.1:8000/audio/${callId}`;

            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.blob();
                })
                .then(blob => {
                    let audioUrl = URL.createObjectURL(blob);
                    let audioPlayer = document.getElementById("audioPlayer");
                    audioPlayer.src = audioUrl;
                    audioPlayer.style.display = "block"; // Show the player
                })
                .catch(error => console.error("Failed to fetch audio:", error));
        }
    </script>

</body>
</html>
    """

# ==============================
# Employee Endpoints
# ==============================
@app.post("/admin/employee")
async def add_employee(
    name: str = Form(...), 
    email: str = Form(...), 
    unique_employee_id: int = Form(...)
):
    employee_id = await db.add_employee(name, email, unique_employee_id)
    return {"employee_id": employee_id}

@app.get("/admin/employees")
async def get_all_employees():
    employees = await db.db.employees.find().to_list(None)
    for emp in employees:
        emp["_id"] = str(emp["_id"])
    return {"employees": employees}

@app.delete("/admin/employee/{unique_employee_id}")
async def delete_employee(unique_employee_id: int):
    success = await db.delete_employee(unique_employee_id)
    return {"success": success}

@app.put("/admin/employee/{unique_employee_id}")
async def edit_employee(
    unique_employee_id: int, 
    name: str = Form(None), 
    email: str = Form(None)
):
    success = await db.edit_employee(unique_employee_id, name, email)
    return {"success": success}

@app.get("/employee/{unique_employee_id}")
async def search_employee(unique_employee_id: int):
    employee = await db.search_employee(unique_employee_id)
    return {"employee": employee}

# ==============================
# Call Endpoints
# ==============================
@app.post("/admin/call/{unique_employee_id}")
async def add_call(
    unique_employee_id: int, 
    duration: int = Form(...),
    audio_file: UploadFile = File(...)
):
    call_id, file_id = await db.add_call(unique_employee_id, duration, audio_file.file)
    return {"call_id": call_id, "file_id": file_id}


@app.delete("/admin/call/{call_id}")
async def remove_call(call_id: int):
    success = await db.remove_call(call_id)
    return {"success": success}

@app.get("/call/{call_id}")
async def get_call(call_id: int):
    call = await db.get_call(call_id)
    return {"call": call}

@app.put("/call/{call_id}")
async def update_call_analysis(
    call_id: int, 
    numerical_score: float = Form(...)
):
    success = await db.update_call_analysis(call_id, numerical_score)
    return {"success": success}

# ==============================
# Analysis Endpoints
# ==============================
@app.post("/admin/analysis/{call_id}")
async def add_analysis(
    call_id: int,
    scorecard_a: str = Form(...),
    scorecard_b: str = Form(...),
    final_score: str = Form(...),
    transcript: str = Form("")
):
    analysis_id = await db.add_analysis(call_id, scorecard_a, scorecard_b, final_score)
    return {"analysis_id": analysis_id}

@app.get("/analysis/{call_id}")
async def get_analysis(call_id: int):
    analysis = await db.get_analysis(call_id)
    return {"analysis": analysis}

@app.put("/analysis/{call_id}")
async def update_analysis(
    call_id: int,
    scorecard_a: str = Form(None),
    scorecard_b: str = Form(None),
    final_score: str = Form(None),
    transcript: str = Form(None)
):
    success = await db.update_analysis(call_id, scorecard_a, scorecard_b, final_score, transcript)
    return {"success": success}

@app.delete("/analysis/{call_id}")
async def delete_analysis(call_id: int):
    success = await db.delete_analysis(call_id)
    return {"success": success}

# ==============================
# Audio Endpoints
# ==============================
@app.get("/audio/{call_id}")
async def get_audio(call_id: int):
    audio_stream = await db.get_audio(call_id)
    if not audio_stream:
        return {"error": "Audio not found"}
    return audio_stream

# ==============================
# FastAPI Server Run
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
