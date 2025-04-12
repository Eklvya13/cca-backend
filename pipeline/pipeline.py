import asyncio
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.audio_processor import audio_processor
from pipeline.analyzer import analyzer_main
from pipeline.scorecard import report_main
from utils import save_dics_list_to_json
from database import get_db

db = get_db() # ✅ initialize it once

def build_analysis_object(
    call_id: str,
    scorecard_a: dict,
    scorecard_b: dict,
    transcript: list,
    final_markdown: str,
    audio_filename: str
) -> dict:
    score_a = scorecard_a.get("final_competence_score")
    numerics_b = scorecard_b.get("numerics", [])
    score_b = scorecard_b.get("final")

    cleaned_numerics = [
        {
            "real_emotion": entry["real_emotion"],
            "absolute_emotion": entry["absolute_emotion"],
            "emotion_score_smoothed": entry["emotion_score_smoothed"]
        }
        for entry in numerics_b
    ]

    final_score = round((score_a + score_b) / 2, 2)

    return {
        "call_id": call_id,
        "final_score": final_score,
        "transcript": transcript,
        "audio_filename": audio_filename,
        "scorecard_a": {
            "score": score_a,
            "parameters": {
                "clarity_score": scorecard_a.get("clarity_score"),
                "knowledge_score": scorecard_a.get("knowledge_score"),
                "confidence_score": scorecard_a.get("confidence_score"),
                "empathy_score": scorecard_a.get("empathy_score"),
                "resolution_score": scorecard_a.get("resolution_score"),
            }
        },
        "scorecard_b": {
            "score": score_b,
            "numerics": cleaned_numerics
        },
        "final_markdown": final_markdown
    }

async def save_analysis_to_db(db_manager, analysis_object: dict):
    call_id = analysis_object["call_id"]
    final_score = analysis_object["final_score"]

    result = await db_manager.db.analysis_results.insert_one(analysis_object)

    await db_manager.db.calls.update_one(
        {"call_id": call_id},
        {"$set": {
            "isAnalysed": True,
            "numerical_score": final_score
        }}
    )

    return str(result.inserted_id)

async def run_pipeline(call_id: str, employee_unique_id: int):
    print(f"Starting analysis for call {call_id}")

    call_data = await db.db.calls.find_one({"call_id": call_id})
    audio_filename = call_data["audio_filename"]

    isolated_file, transcript_result = audio_processor(call_id=call_id, employee_unique_id=employee_unique_id)

    save_dics_list_to_json(transcript_result, call_id)
    
    if not isolated_file:
        print(f"Error: No audio file found for call {call_id}")
        return
    print(f"Completed diarization STAGE for call {call_id}")

    scorecard_a, scorecard_b = analyzer_main(transcript=transcript_result, call_id=call_id)
    save_dics_list_to_json(scorecard_a, f"{call_id}_scorecard_a")
    save_dics_list_to_json(scorecard_b, f"{call_id}_scorecard_b")
    print(f"Generated scorecards for call {call_id}")

    final_report = report_main(scorecard_a=scorecard_a, scorecard_b=scorecard_b)
    print(f"Finalized report for call {call_id}")

    analysis_object = build_analysis_object(
        call_id=call_id,
        scorecard_a=scorecard_a,
        scorecard_b=scorecard_b,
        transcript=transcript_result,
        final_markdown=final_report,
        audio_filename=audio_filename
    )

    save_dics_list_to_json(analysis_object, "test.json")

    analysis_id = await save_analysis_to_db(db_manager=db, analysis_object=analysis_object)
    print(analysis_id)
    print(f"Analysis Process complete for call {call_id}")
