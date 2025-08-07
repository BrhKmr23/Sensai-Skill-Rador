# Bouncer: AI-Powered Candidate Pre-Screener

Bouncer is a FastAPI-based backend for automated candidate pre-screening using Google Gemini 2.5 Pro. It generates technical interview questions, evaluates candidate answers, and supports video/audio uploads for further analysis.

## Features

- **AI-Generated Interview Questions:** Generates relevant questions based on job role, required skills, and experience level.
- **Automated Answer Evaluation:** Uses Gemini to score candidate answers and provide explanations.
- **Video/Audio Uploads:** Candidates can upload video or audio responses for each question.
- **Batch Processing:** Supports background processing of candidate submissions.
- **CORS Enabled:** Ready for integration with any frontend.

## Project Structure

```
bouncer-test/
├── main.py                # FastAPI backend
├── first_phase.py         # Batch processing utilities
├── requirements.txt       # Python dependencies
├── static/                # Static HTML files for recruiter/candidate
├── answers/               # Uploaded candidate responses (auto-created)
└── ...
```

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/BrhKmr23/Sensai-Skill-Rador.git
cd bouncer-test
```

### 2. Install Dependencies

```sh
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Do not commit your `.env` file!**

### 4. Run the Server

```sh
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### Recruiter

- `POST /recruiter/submit-job-role` — Generate interview questions

### Candidate

- `GET /candidate/questions/{session_id}` — Get a question
- `POST /candidate/answer` — Submit and evaluate an answer
- `POST /candidate/upload-video` — Upload video response
- `POST /candidate/upload-audio` — Upload audio response
- `GET /candidate/process/{candidate_id}` — Start batch processing

## Notes

- Requires a valid Google Gemini API key.
- All candidate uploads are stored in the `answers/` directory.
- Static HTML files for recruiter and candidate are in `static/`.

## License

MIT License
