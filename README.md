# Call Center Analytics Backend

## Overview

This project is a backend system built with FastAPI to analyze call center recordings. It processes audio files, transcribes them, and performs advanced analyses to evaluate agent competence and caller emotions. The backend integrates with a React-based frontend for visualization and interaction.

## Key Features

- **Audio Upload & Storage**: Audio files are uploaded and stored in Google Cloud Storage (GCS). Public URLs are saved in MongoDB.
- **Transcription**: Uses Google Cloud Speech-to-Text with speaker diarization for transcription, including sentence-level timestamps and speaker tagging.
- **Competence Analysis**: Evaluates agent performance using Google Gemini API (LLM-based).
- **Emotion Analysis**: Analyzes caller emotions using a remote emotion classification API, categorizing emotions into `absolute_emotion` and `real_emotion`.
- **Final Scoring**: Combines competence and emotion analyses into a single score.

## Tech Stack

| Component               | Technology                     |
|-------------------------|---------------------------------|
| Backend Framework       | FastAPI (Python)               |
| Database                | MongoDB Atlas                  |
| Storage                 | Google Cloud Storage (GCS)     |
| Transcription           | Google Cloud Speech-to-Text    |
| Competence Analysis     | Google Gemini API              |
| Emotion Analysis        | External Emotion API           |

## Setup Instructions

### Prerequisites
- Python 3.9+
- MongoDB Atlas account
- Google Cloud account with GCS and Speech-to-Text enabled
- API keys for Google Gemini and Emotion API

### Environment Variables
Create a `.env` file with the following:
```
MONGO_URI=<your_mongodb_connection_string>
GCS_BUCKET_NAME=<your_gcs_bucket_name>
GOOGLE_APPLICATION_CREDENTIALS=<path_to_google_credentials_json>
GEMINI_API_KEY=<your_google_gemini_api_key>
EMOTION_API_KEY=<your_emotion_api_key>
```

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/cca-backend.git
    cd cca-backend
    ```
2. Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3. Run database migrations (if applicable).

### Running the Application
Start the FastAPI server:
```bash
uvicorn main:app --reload
```

## Project Structure
```
## Project Structure

```
cca-backend/
├── assets/                 # Contains audio and transcript files
│   ├── isolated/           # Processed audio files
│   ├── recordings/         # Raw audio recordings
│   └── transcripts/        # Transcription files
├── pipeline/               # Core processing pipeline
│   ├── __init__.py         # Package initializer
│   ├── analyzer.py         # Competence and emotion analysis logic
│   ├── audio_processor.py  # Audio processing utilities
│   ├── pipeline.py         # Main pipeline orchestration
│   ├── prompts.py          # Prompt templates for analysis
│   └── scorecard.py        # Scoring logic
├── database.py             # MongoDB + GCS Bucket integration
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── tasks.py                # Background task definitions
├── utils.py                # Utility functions
└── README.md               # Project documentation
```

## API Endpoint Summary

| Endpoint                  | Method | Description                          |
|---------------------------|--------|--------------------------------------|
| `/upload`                 | POST   | Uploads an audio file to GCS         |
| `/transcribe/{call_id}`   | GET    | Transcribes audio and saves results  |
| `/analyze/{call_id}`      | POST   | Performs competence and emotion analysis |
| `/results/{call_id}`      | GET    | Fetches analysis results             |

## Analysis Pipeline

1. **Audio Upload**: Audio files are uploaded and stored in GCS.
2. **Transcription**: Google Cloud STT transcribes the audio with speaker diarization.
3. **Competence Analysis**: Agent speech is analyzed using Google Gemini API.
4. **Emotion Analysis**: Caller audio is sliced and analyzed for emotions.
5. **Final Scoring**: Results are combined into a final score.

## Security Notes

- **Signed GCS URLs**: Ensure audio files are accessed via signed URLs to prevent unauthorized access.
- **Secured MongoDB**: Use strong credentials and IP whitelisting for MongoDB Atlas.
- **Environment Variables**: Store sensitive keys in `.env` and avoid committing them to version control.

---

## Author

**Hari Acharya**  
[GitHub Profile](https://github.com/Eklvya13)  