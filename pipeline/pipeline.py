import asyncio
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.audio_processor import audio_processor
from pipeline.analyzer import analyzer_main
from utils import save_dics_list_to_json

async def run_pipeline(call_id: str, employee_unique_id: int):
    print(f"Starting analysis for call {call_id}")

    # Step 1: Diarization + Splitting
    isolated_file, transcript_result = audio_processor(call_id=call_id, employee_unique_id=employee_unique_id)

    save_dics_list_to_json(transcript_result, call_id)
    
    if not isolated_file:
        print(f"Error: No audio file found for call {call_id}")
        return
    print(f"Completed diarization STAGE for call {call_id}")

    # Step 2: Scorecard Generation (A + B)
    scorecard_a, scorecard_b = analyzer_main(transcript=transcript_result, call_id=call_id)
    # save scorecard a and b
    save_dics_list_to_json(scorecard_a, f"{call_id}_scorecard_a")
    save_dics_list_to_json(scorecard_b, f"{call_id}_scorecard_b")
    print(f"Generated scorecards for call {call_id}")

    # Step 3: Final Report
    await asyncio.sleep(5)
    print(f"Finalized report for call {call_id}")

    print(f"Analysis complete for call {call_id}")
 