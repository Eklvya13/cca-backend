import json
import numpy as np
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent / "assets"
TRANCRIPT_DIR = ASSET_DIR / "transcripts"

cors_origins = [
    "http://localhost:3000",  # Your Next.js frontend (local)
    "http://127.0.0.1:3000",  # Alternative localhost
     # (Add your production frontend domain here)
]


# Emotion polarity mapping
POLARITY_MAP = {
    "angry": "negative",
    "disgust": "negative",
    "fear": "negative",
    "sad": "negative",
    "happy": "positive",
    "surprise": "positive",
    "neutral": "neutral",
}

def slice_audio(audio, sr, slice_duration, rms_threshold):
    slice_samples = int(slice_duration * sr)
    total_samples = len(audio)
    slices = []

    for start in range(0, total_samples, slice_samples):
        end = min(start + slice_samples, total_samples)
        audio_slice = audio[start:end]

        rms = np.sqrt(np.mean(audio_slice ** 2))
        is_silent = rms < rms_threshold

        if not is_silent:
            slices.append({
                "start_time": round(start / sr, 2),
                "end_time": round(end / sr, 2),
                "audio_slice": audio_slice
            })

    return slices


def scorecard_b_numerics_to_text(scorecard_b_numerics):
    ret = ""
    ret += "start_time,end_time,raw_emotion,absolute_emotion,raw_emotion_score,smoothed_emotion_score\n"
    for entry in scorecard_b_numerics:
        ret += f"{entry['start_time']},{entry['end_time']},{entry['real_emotion']},{entry['absolute_emotion']},{entry['emotion_score_raw']},{entry['emotion_score_smoothed']}\n"
    return ret

def save_markdown(md, file_path):
    """Save the given markdown text to a .md file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md)
    except Exception as e:
        print(f"Error saving markdown file: {e}")


def save_scorecard_b_numerics(scorecard, file_path):
    with open(file_path, 'w') as f:
        for entry in scorecard:
            f.write(f"{entry['start_time']},{entry['end_time']},{entry['real_emotion']},"
                    f"{entry['absolute_emotion']},{entry['emotion_score_raw']},"
                    f"{entry['emotion_score_smoothed']}\n")


def merged_transcript_to_text(merged_transcripts):
    transcript_text = ''
    for entry in merged_transcripts:
        if all(key in entry for key in ['speaker', 'sentence', 'start_time', 'end_time']):
            line = f"{entry['speaker']}: {entry['sentence']} (Start: {entry['start_time']}, End: {entry['end_time']})\n"
            transcript_text += line
        else:
            print(f"Missing keys in entry: {entry}")
    return transcript_text

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