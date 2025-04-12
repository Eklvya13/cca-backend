import librosa
import torch
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import POLARITY_MAP, slice_audio, save_scorecard_b_numerics, scorecard_b_numerics_to_text, merged_transcript_to_text
from pipeline.prompts import Gemini

from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

# Constants
SLICE_DURATION = 5
RMS_THRESHOLD = 0.01

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class EmotionDetectorLocal:
    def __init__(self):
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
            "r-f/wav2vec-english-speech-emotion-recognition"
        )
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(
            "r-f/wav2vec-english-speech-emotion-recognition"
        ).to(DEVICE)
        self.model.eval()

    def predict_batch(self, audio_slices, sampling_rate):
        inputs = self.feature_extractor(
            audio_slices,
            sampling_rate=sampling_rate,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=250000
        )
        input_values = inputs["input_values"].to(DEVICE)
        attention_mask = inputs["attention_mask"].to(DEVICE)

        with torch.no_grad():
            outputs = self.model(input_values=input_values, attention_mask=attention_mask)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        results = []
        for i in range(len(audio_slices)):
            confidence, predicted_label = torch.max(probs[i], dim=-1)
            emotion = self.model.config.id2label[predicted_label.item()]
            emotion_score = round(confidence.item(), 4)
            absolute_emotion = POLARITY_MAP.get(emotion, "neutral")

            results.append({
                "real_emotion": emotion,
                "absolute_emotion": absolute_emotion,
                "emotion_score": emotion_score,
            })

        return results

    def predict_in_mini_batches(self, audio_slices, batch_size=4, sampling_rate=16000):
        results = []
        for i in range(0, len(audio_slices), batch_size):
            batch = audio_slices[i:i + batch_size]
            results.extend(self.predict_batch(batch, sampling_rate))
        return results


def generate_scorecard_b_numeric(result, slice_duration=5.0, alpha=0.3):
    # Generate a cleaned and smoothed version of Scorecard B.

    final_scorecard = []
    smoothed_score = 0.0

    def get_absolute_emotion(real_emotion):
        mapping = {
            "angry": "negative",
            "disgust": "negative",
            "fear": "negative",
            "sad": "negative",
            "happy": "positive",
            "surprise": "positive",
            "neutral": "neutral",
        }
        return mapping.get(real_emotion.lower(), "neutral")

    def polarity_score(abs_emotion, raw_score):
        if abs_emotion == "positive":
            return +raw_score
        elif abs_emotion == "negative":
            return -raw_score
        else:
            return 0.0

    result = sorted(result, key=lambda x: x["start_time"])
    expected_start = 0.0

    for entry in result:
        start = round(entry["start_time"], 3)
        end = round(entry["end_time"], 3)

        # Fill in any missing silent/neutral slices
        while round(expected_start, 3) < round(start, 3):
            raw_score = 0.0
            smoothed_score = alpha * raw_score + (1 - alpha) * smoothed_score
            final_scorecard.append({
                "start_time": expected_start,
                "end_time": expected_start + slice_duration,
                "real_emotion": "neutral",
                "absolute_emotion": "neutral",
                "emotion_score_raw": raw_score,
                "emotion_score_smoothed": round(smoothed_score, 4),
            })
            expected_start += slice_duration

        # Actual (non-gap) entry
        real_emotion = entry["real_emotion"]
        abs_emotion = get_absolute_emotion(real_emotion)
        raw_score = polarity_score(abs_emotion, entry["emotion_score"])
        smoothed_score = alpha * raw_score + (1 - alpha) * smoothed_score

        final_scorecard.append({
            "start_time": start,
            "end_time": end,
            "real_emotion": real_emotion,
            "absolute_emotion": abs_emotion,
            "emotion_score_raw": round(raw_score, 4),
            "emotion_score_smoothed": round(smoothed_score, 4),
        })

        expected_start = end

    return final_scorecard

def run_scorecard_a(transcript, call_id):
    transcript_text = merged_transcript_to_text(transcript)
    summary = Gemini().generate_summary_with_data(transcript_text, 'scorecard_a').replace("\n```", "").replace("```json\n", "")
    return eval(summary)

def run_scorecard_b_local(call_id):
    audio_path = os.path.join("assets", "isolated", f"{call_id:03d}_isolated.wav")
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    audio_slices = slice_audio(audio, sr, SLICE_DURATION, RMS_THRESHOLD)

    detector = EmotionDetectorLocal()
    results = detector.predict_in_mini_batches([slice["audio_slice"] for slice in audio_slices])

    scorecard_b_raw = []
    for i, result in enumerate(results):
        scorecard_b_raw.append({
            "start_time": audio_slices[i]["start_time"],
            "end_time": audio_slices[i]["end_time"],
            "real_emotion": result["real_emotion"],
            "absolute_emotion": result["absolute_emotion"],
            "emotion_score": result["emotion_score"],
        })
    
    scorecard_b_numerics = generate_scorecard_b_numeric(scorecard_b_raw, SLICE_DURATION, alpha=0.3)
    scorecard_b_text = Gemini().generate_summary_with_data(scorecard_b_numerics_to_text(scorecard_b_numerics=scorecard_b_numerics), "scorecard_b")
    scorecard_b = {'numerics' : scorecard_b_numerics, 'text' : scorecard_b_text, 'final': compute_final_scorecard_b_score(scorecard_b_numerics=scorecard_b_numerics)}
    # Save the scorecard to a JSON file
    save_scorecard_b_numerics(scorecard=scorecard_b["numerics"], file_path=os.path.join("assets", "scorecards", f"{call_id:03d}_scorecard_b.csv"))
    
    return scorecard_b

def analyzer_main(transcript, call_id):
    scorecard_a = run_scorecard_a(transcript, call_id)
    scorecard_b = run_scorecard_b_local(call_id)
    return scorecard_a, scorecard_b

def compute_final_scorecard_b_score(scorecard_b_numerics, min_val=-0.3, max_val=0.3):
    smoothed_scores = [
        entry["emotion_score_smoothed"]
        for entry in scorecard_b_numerics
        if "emotion_score_smoothed" in entry
    ]

    if not smoothed_scores:
        return 0.5  # Neutral default if data is missing

    avg_smoothed = sum(smoothed_scores) / len(smoothed_scores)

    # Clip and normalize
    avg_smoothed = max(min(avg_smoothed, max_val), min_val)
    normalized_score = (avg_smoothed - min_val) / (max_val - min_val)

    return round(normalized_score, 4)

def main():
    call_id = 14
    scorecard_a, scorecard_b = analyzer_main(sample_merged_transcript, call_id)
    print(scorecard_a , scorecard_b)

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

if __name__ == '__main__':
    main()