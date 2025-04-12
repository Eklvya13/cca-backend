from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from database import DatabaseManager
from tasks import start_analysis
from utils import cors_origins

app = FastAPI(title="Call Center Analytics API")
db = DatabaseManager()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# Welcome Page (TEMP)
# ===========================
@app.get("/welcome-temp", response_class=HTMLResponse)
async def welcome():
    return """
    <html><head><title>API Docs</title></head>
    <body><h2><a href='/docs'>Go to Swagger Docs</a></h2></body>
    </html>
    """

# ===========================
# Employee Endpoints
# ===========================
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

@app.get("/employee/{unique_employee_id}")
async def get_employee(unique_employee_id: int):
    employee = await db.get_employee(unique_employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee": employee}

@app.put("/admin/employee/{unique_employee_id}")
async def update_employee(
    unique_employee_id: int,
    name: str = Form(None),
    email: str = Form(None)
):
    success = await db.edit_employee(unique_employee_id, name, email)
    return {"success": success}

@app.delete("/admin/employee/{unique_employee_id}")
async def delete_employee(unique_employee_id: int):
    success = await db.delete_employee(unique_employee_id)
    return {"success": success}

# ===========================
# Call Endpoints
# ===========================
@app.post("/admin/call/{unique_employee_id}")
async def upload_call(
    unique_employee_id: int,
    duration: int = Form(...),
    audio_file: UploadFile = File(...)
):
    call_id, filename = await db.add_call(unique_employee_id, duration, audio_file.file)
    return {"call_id": call_id, "file": filename}

@app.get("/call/{call_id}")
async def fetch_call(call_id: int):
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return {"call": call}

@app.delete("/admin/call/{call_id}")
async def delete_call(call_id: int):
    success = await db.remove_call(call_id)
    return {"success": success}

@app.put("/call/{call_id}")
async def update_call_score(
    call_id: int,
    numerical_score: float = Form(...)
):
    success = await db.update_call_analysis(call_id, numerical_score)
    return {"success": success}

# ===========================
# Audio Endpoints
# ===========================
@app.get("/audio/{call_id}")
async def get_audio_url(call_id: int):
    url = await db.get_audio_url(call_id)
    if not url:
        raise HTTPException(status_code=404, detail="Audio not found")
    return {"url": url}

# ===========================
# Analysis Endpoints
# ===========================
@app.post("/admin/analysis/{call_id}")
async def save_analysis(
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
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
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

# ===========================
# Analysis Trigger (Background)
# ===========================
@app.post("/analyze/{call_id}")
def trigger_analysis(call_id: int, employee_unique_id: int, background_tasks: BackgroundTasks):
    return start_analysis(background_tasks, call_id, employee_unique_id)

# ===========================
# Summary for Frontend Dashboard
# ===========================
@app.get("/employee/{employee_id}/summary")
async def get_employee_summary(employee_id: int):
    calls = await db.db.calls.find({"employee_unique_id": employee_id}).to_list(None)
    if not calls:
        raise HTTPException(status_code=404, detail="No calls found")

    total_calls = len(calls)
    durations = [c.get("duration", 0) for c in calls]
    scores = [c.get("numerical_score", 0) or 0 for c in calls]

    avg_duration = round(sum(durations) / total_calls, 2)
    avg_score = round(sum(scores) / total_calls, 2)

    def get_emotion(score):
        return "positive" if score >= 75 else "neutral" if score >= 50 else "negative"

    emotion_dist = {"positive": 0, "neutral": 0, "negative": 0}
    for score in scores:
        emotion_dist[get_emotion(score)] += 1
    emotion_distribution = {
        k: round((v / total_calls) * 100, 2) for k, v in emotion_dist.items()
    }

    call_details = [
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
        "calls": call_details
    }

@app.get("/admin/calls")
async def get_all_calls_summary():
    calls = await db.db.calls.find().to_list(None)

    result = []
    for call in calls:
        result.append({
            "call_id": call.get("call_id"),
            "employee_unique_id": call.get("employee_unique_id"),
            "call_duration": call.get("duration"),
            "numerical_score": call.get("numerical_score", 0),
            "is_analyzed": call.get("isAnalysed", False),
            "audio_filename": call.get("audio_filename", "")
        })

    return {"calls": result}


@app.get("/call-analysis/{call_id}")
async def get_analysis_by_call_id(call_id: int):
    analysis = await db.db.analysis_results.find_one({"call_id": call_id})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get signed URL from GCS via db manager
    audio_url = await db.get_audio_url(call_id)

    response = {
        "call_id": analysis["call_id"],
        "final_score": analysis.get("final_score", 0),
        "transcript": analysis.get("transcript", ""),
        "link": audio_url,
        "scorecard_B": {
            "score": analysis.get("scorecard_b", {}).get("score", 0),
            "numerics": analysis.get("scorecard_b", {}).get("numerics", [])
        },
        "scorecard_A": {
            "score": analysis.get("scorecard_a", {}).get("score", 0),
            "individual_parameters": analysis.get("scorecard_a", {}).get("parameters", {})
        },
        "final_markdown": analysis.get("final_markdown", "")
    }

    return response


# ===========================
# Run the App
# ===========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
