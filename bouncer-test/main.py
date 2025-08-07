from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import os
import google.generativeai as genai
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import re
import shutil
import sys
import importlib.util

app = FastAPI()

# CORS middleware for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory session store
sessions: Dict[str, Dict] = {}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set")
# Gemini API config
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "models/gemini-2.5-flash"
model = genai.GenerativeModel(model_name=GEMINI_MODEL)

# Import the batch_convert_and_transcribe function from first_phase.py
spec = importlib.util.spec_from_file_location("first_phase", "first_phase.py")
first_phase = importlib.util.module_from_spec(spec)
sys.modules["first_phase"] = first_phase
spec.loader.exec_module(first_phase)

# Gemini API utility
async def call_gemini(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

# Recruiter input model
class RecruiterInput(BaseModel):
    job_role: str
    required_skills: List[str]
    experience_level: str

# Candidate answer model
class CandidateAnswer(BaseModel):
    session_id: str
    question: str
    answer: str

def extract_json(text):
    # Remove code block markers if present
    match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if match:
        return match.group(1)
    return text.strip()

@app.post("/recruiter/submit-job-role")
async def submit_job_role(input: RecruiterInput):
    prompt = (
        "You are an expert technical recruiter. Given the job role, required skills, and experience level, generate a set of 5 interview questions. Each question must test the candidate's knowledge relevant to the job.\n\n"
        f"Job Role: {input.job_role}\n"
        f"Required Skills: {', '.join(input.required_skills)}\n"
        f"Experience Level: {input.experience_level}\n\n"
        "Output ONLY the questions in a numbered list, with NO preamble, NO explanation, and NO extra text."
    )
    try:
        questions_text = await call_gemini(prompt)
        questions = [q.strip().split('. ', 1)[-1] if '. ' in q else q.strip() for q in questions_text.strip().split('\n') if q.strip()]
        if len(questions) < 5:
            raise ValueError(f"Got less than 5 questions: {questions}")
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"questions": questions}
        return {"questions": questions, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

@app.get("/candidate/questions/{session_id}")
async def get_candidate_question(session_id: str, q: int = 0):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    questions = session["questions"]
    if q < 0 or q >= len(questions):
        raise HTTPException(status_code=404, detail="No more questions.")
    return {"question": questions[q], "index": q}

@app.post("/candidate/answer")
async def evaluate_answer(answer: CandidateAnswer):
    prompt = (
        "You are a strict technical interviewer. Given a question and a candidate's answer, evaluate the response on a scale of 1 to 10. Include a 1-2 sentence explanation for the score.\n\n"
        f"Question: {answer.question}\n"
        f"Answer: {answer.answer}\n\n"
        "Give only a JSON response like this:\n"
        "{\n  \"score\": <score>,\n  \"explanation\": \"<brief reason>\"\n}"
    )
    gemini_response = await call_gemini(prompt)
    import json as pyjson
    cleaned = extract_json(gemini_response)
    try:
        result = pyjson.loads(cleaned)
        score = result.get("score")
        explanation = result.get("explanation")
        if score is None or explanation is None:
            raise ValueError
        return {"score": score, "explanation": explanation}
    except Exception:
        raise HTTPException(status_code=500, detail=f"Malformed Gemini evaluation: {gemini_response}")

ANSWERS_DIR = "answers"
os.makedirs(ANSWERS_DIR, exist_ok=True)

@app.post("/candidate/upload-video")
async def upload_video(
    session_id: str = Form(...),
    candidate_id: str = Form(...),
    question: str = Form(...),
    q_index: int = Form(...),
    video: UploadFile = File(...)
):
    try:
        ext = os.path.splitext(video.filename)[1] or ".webm"
        safe_candidate = candidate_id.replace("/", "_")
        candidate_dir = os.path.join(ANSWERS_DIR, safe_candidate)
        os.makedirs(candidate_dir, exist_ok=True)
        filename = f"{q_index+1}{ext}"
        file_path = os.path.join(candidate_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        return {"status": "success", "filename": filename, "candidate_id": candidate_id}
    except Exception as e:
        print("Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.post("/candidate/upload-audio")
async def upload_audio(
    session_id: str = Form(...),
    candidate_id: str = Form(...),
    question: str = Form(...),
    q_index: int = Form(...),
    audio: UploadFile = File(...)
):
    try:
        ext = os.path.splitext(audio.filename)[1] or ".webm"
        safe_candidate = candidate_id.replace("/", "_")
        candidate_dir = os.path.join(ANSWERS_DIR, safe_candidate)
        os.makedirs(candidate_dir, exist_ok=True)
        filename = f"{q_index+1}{ext}"
        file_path = os.path.join(candidate_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        return {"status": "success", "filename": filename, "candidate_id": candidate_id}
    except Exception as e:
        print("Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.get("/candidate/process/{candidate_id}")
async def process_candidate(candidate_id: str, background_tasks: BackgroundTasks):
    # Run the batch conversion and transcription in the background
    background_tasks.add_task(first_phase.batch_convert_and_transcribe, candidate_id)
    return {"status": "processing started", "candidate_id": candidate_id}
