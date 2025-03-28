from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
from database import DatabaseManager

app = FastAPI()
db = DatabaseManager()  # Single instance for now

# Temporary Home Page
@app.get("/welcome-temp", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>Call Center Demo</title></head>
        <body>
            <h1>Welcome to Call Center Analysis</h1>
            <p>This is a temp page. Check out the <a href="/docs">API Docs</a>.</p>
        </body>
    </html>
    """

# API Endpoints
@app.post("/admin/employee")
async def add_employee(name: str, email: str, unique_employee_id: int):
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
async def edit_employee(unique_employee_id: int, name: str = None, email: str = None):
    success = await db.edit_employee(unique_employee_id, name, email)
    return {"success": success}

@app.get("/employee/{unique_employee_id}")
async def search_employee(unique_employee_id: int):
    employee = await db.search_employee(unique_employee_id)
    return {"employee": employee}

@app.post("/admin/call/{unique_employee_id}")
async def add_call(unique_employee_id: int, audio_file: UploadFile, duration: int):
    call_id = await db.add_call(unique_employee_id, audio_file.file, duration)
    return {"call_id": call_id}

@app.delete("/admin/call/{call_id}")
async def remove_call(call_id: str):
    success = await db.remove_call(call_id)
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)