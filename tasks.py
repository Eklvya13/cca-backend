import asyncio
from fastapi import BackgroundTasks
from pipeline.pipeline import run_pipeline

# Global lock to ensure only one analysis runs at a time
analysis_lock = asyncio.Lock()

async def sequential_pipeline(call_id: str, employee_unique_id: int):
    async with analysis_lock:  # Ensures only one analysis runs at a time
        await run_pipeline(call_id, employee_unique_id)  # Assuming `run_pipeline` is async

def start_analysis(background_tasks: BackgroundTasks, call_id: int, employee_unique_id: int):
    background_tasks.add_task(sequential_pipeline, call_id, employee_unique_id)
    return {"message": "Analysis started", "call_id": call_id}
