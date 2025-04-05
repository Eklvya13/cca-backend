import os
from pydub import AudioSegment
from google.cloud import speech
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve(strict=True).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ISOLATED_DIR = ASSETS_DIR / "isolated"
ISOLATED_DIR.mkdir(parents=True, exist_ok=True)

def get_transcribe_result(audio_file: str):
    """Transcribe the given audio file from Google Cloud Storage using Google Speech-to-Text."""
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri='gs://cca-backend-calls/calls/' + audio_file)

    diarization_config = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=2,
            max_speaker_count=2,
        )

    sst_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US",
            enable_automatic_punctuation=True,
            diarization_config=diarization_config,
            model="phone_call",
            enable_word_time_offsets=False,  
        )

    response = client.long_running_recognize(config=sst_config, audio=audio)
    operation = response.result(timeout=600)

    # Extract and return formatted results
    transcript_data = []
    for result in operation.results:
        alternative = result.alternatives[0]
        transcript_data.append({
            "transcript": alternative.transcript,
            "confidence": alternative.confidence,
            "words": [
                {
                    "word": word.word,
                    "start_time": word.start_time.total_seconds(),
                    "end_time": word.end_time.total_seconds(),
                    "speaker_tag": word.speaker_tag if hasattr(word, 'speaker_tag') else None,
                } for word in alternative.words
            ],
        })
    return transcript_data

def merge_transcript_by_speaker(transcript_result):
    merged_transcript = []
    current_speaker = None
    current_sentence = []
    cur_start_time = None
    cur_end_time = None

    for word in transcript_result[-1]['words']:
        speaker = word['speaker_tag']
        if speaker != current_speaker:
            if current_speaker is not None:
                merged_transcript.append({
                    "speaker": current_speaker,
                    "sentence": ' '.join(current_sentence),
                    "start_time": cur_start_time,
                    "end_time": cur_end_time,
                })
            current_speaker = speaker
            current_sentence = [word['word']]
            cur_start_time = word['start_time']
            cur_end_time = word['end_time']
        else:
            if word['start_time'] - cur_end_time > 2.5: #2.5 seconds gap
                # current sentence and start a new one
                merged_transcript.append({
                    "speaker": current_speaker,
                    "sentence": ' '.join(current_sentence),
                    "start_time": cur_start_time,
                    "end_time": cur_end_time,
                })
                current_sentence = [word['word']]
                cur_start_time = word['start_time']
                cur_end_time = word['end_time']
            
            else:
                current_sentence.append(word['word'])
                cur_end_time = word['end_time']
    
    # last sentence
    if current_sentence:
        merged_transcript.append({
            "speaker": current_speaker,
            "sentence": ' '.join(current_sentence),
            "start_time": cur_start_time,
            "end_time": cur_end_time,
        })
    
    return merged_transcript

def isolate_speaker_audio(call_id: str, diarization_result: list, save_dir=ISOLATED_DIR):
    """
   Keeps only the selected speaker's voice and mutes everything else in a call recording.
   Returns: Path to the saved isolated audio file.
    """
    call_id_str = f"{call_id:03}"

    # Load the original audio file
    audio_path = Path(ASSETS_DIR) / "recordings" / f"{call_id_str}.wav"
    
    audio = AudioSegment.from_wav(audio_path)

    # Identify the target speaker (2)
    target_speaker = 2  # Assuming the second speaker is the target speaker

    # Create a silent audio track of the same length
    isolated_audio = AudioSegment.silent(duration=len(audio))

    # Iterate through diarization results and keep only the target speaker
    for segment in diarization_result:
        speaker = segment["speaker"]
        start_time = int(segment["start_time"] * 1000)  # Convert to milliseconds for both
        end_time = int(segment["end_time"] * 1000) 

        if speaker == target_speaker and (end_time - start_time) >= 1000:
            # Overlay the original segment onto the silent audio
            isolated_audio = isolated_audio.overlay(audio[start_time:end_time], position=start_time)

    # Save the isolated audio file
    isolated_path = Path(save_dir) / f"{call_id_str}_isolated.wav"
    isolated_audio.export(isolated_path, format="wav")

    print(f"Isolated speaker audio saved at: {isolated_path}")
    return isolated_path

def audio_processor(call_id, employee_unique_id):
    call_id_str = f"{call_id:03}"
    transcript_result = get_transcribe_result(f'{employee_unique_id}_{call_id_str}.wav')
    
    merged_transcript = merge_transcript_by_speaker(transcript_result)

    # Example merged transcript format for testing purposes
    # merged_transcript = sample_merged_transcript

    isolated_file_path = isolate_speaker_audio(call_id, merged_transcript, save_dir=ISOLATED_DIR)

    return isolated_file_path, merged_transcript

if __name__ == "__main__":
    call_id = 3
    employee_unique_id = 1001
    fp, mt = audio_processor(call_id, employee_unique_id)
    print(fp)
    print(mt)

sample_merged_transcript = [
    {
        "speaker": 1,
        "start_time": 0.0,
        "end_time": 6.2,
        "text": "Hello, thank you for calling. How can I assist you today?"
    },
    {
        "speaker": 2,
        "start_time": 6.5,
        "end_time": 12.3,
        "text": "Hi, I'm having an issue with my internet connection, it's been really slow."
    },
    {
        "speaker": 1,
        "start_time": 12.5,
        "end_time": 20.0,
        "text": "I'm sorry to hear that. Let me check your account. Can I have your registered phone number?"
    },
    {
        "speaker": 2,
        "start_time": 20.3,
        "end_time": 26.1,
        "text": "Yes, it's 555-1234. It's the same number I used to call today."
    },
    {
        "speaker": 1,
        "start_time": 26.4,
        "end_time": 32.0,
        "text": "Thank you. I see the account here. There was an outage reported in your area earlier."
    },
    {
        "speaker": 2,
        "start_time": 32.4,
        "end_time": 39.1,
        "text": "Oh, that makes sense. Do you know when it’ll be fixed?"
    },
    {
        "speaker": 1,
        "start_time": 39.3,
        "end_time": 46.7,
        "text": "It should be resolved within the next two hours. We apologize for the inconvenience."
    },
    {
        "speaker": 2,
        "start_time": 47.0,
        "end_time": 53.2,
        "text": "Alright, thanks for letting me know. I’ll wait for it to come back."
    },
    {
        "speaker": 1,
        "start_time": 53.5,
        "end_time": 58.8,
        "text": "Is there anything else I can assist you with today?"
    },
    {
        "speaker": 2,
        "start_time": 59.0,
        "end_time": 63.2,
        "text": "No, that was all. Thanks again."
    },
    {
        "speaker": 1,
        "start_time": 63.5,
        "end_time": 66.5,
        "text": "You're welcome. Have a great day!"
    }
]