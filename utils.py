import json
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent / "assets"
TRANCRIPT_DIR = ASSET_DIR / "transcripts"

cors_origins = [
    "http://localhost:3000",  # Your Next.js frontend (local)
    "http://127.0.0.1:3000",  # Alternative localhost
     # (Add your production frontend domain here)
]

def save_dics_list_to_json(dict_list, call_id):
    """Save a list of dictionaries to a JSON file."""
    try:
        with open( Path(TRANCRIPT_DIR) / f"{call_id}.json" , 'w', encoding='utf-8') as f:
            json.dump(dict_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def convert_to_mono(audio_file):
    """Convert audio to mono if not already."""
    try:
        from pydub import AudioSegment
        from io import BytesIO
    except ImportError:
        raise ImportError("pydub is required for audio processing. Install it with 'pip install pydub'.")
    
    audio = AudioSegment.from_file(audio_file)
    if audio.channels > 1:
        audio = audio.set_channels(1)

    # Save the mono audio to a BytesIO object
    mono_audio_file = BytesIO()
    audio.export(mono_audio_file, format="wav")
    mono_audio_file.seek(0)
    audio_file = mono_audio_file

    return audio_file