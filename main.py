from fastapi import FastAPI, UploadFile, Form, File, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import DatabaseManager
from tasks import start_analysis
from utils import cors_origins

app = FastAPI()
db = DatabaseManager()


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Allow only specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Temporary Home Page
@app.get("/welcome-temp", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aur Laundo</title>
</head>
<body>

    <a href="/docs"><h2>Here Lies the Docs</h2></a>

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
    employee = await db.get_employee(unique_employee_id)
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
    call_id, filename = await db.add_call(unique_employee_id, duration, audio_file.file)
    return {"call_id": call_id, "file_id": filename}


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
    file_name= await db.get_audio_url(call_id)
    if not file_name:
        return {"error": "Audio not found"}
    return file_name


@app.post("/analyze/{call_id}")
def analyze_call(call_id: int, employee_unique_id: int, background_tasks: BackgroundTasks):
    return start_analysis(background_tasks, call_id, employee_unique_id)

# ==============================
# FastAPI Server Run
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
