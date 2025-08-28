import os, json, time
from typing import Tuple
import requests
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_BASE = ('https://generativelanguage.googleapis.com/v1beta/models/'
               'gemini-2.0-flash:generateContent')

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF using PyPDF2. Works for text PDFs (not OCR).
    """
    text_chunks = []
    try:
        reader = PdfReader(file_path)
        for p in reader.pages:
            txt = p.extract_text()
            if txt:
                text_chunks.append(txt)
    except Exception as e:
        return f"[PDF parse error] {e}"
    return "\n\n".join(text_chunks)

def call_gemini(prompt: str, temperature: float = 0.2, max_output_tokens: int = 512) -> dict:
    """
    Minimal wrapper for the Gemini REST endpoint.
    Expects GEMINI_API_KEY set in environment.
    Returns parsed JSON response (or raises).
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        raise ValueError('GEMINI_API_KEY is not set. Put it in a .env file.')

    params = {'key': api_key}
    body = {
        'prompt': {
            'text': prompt
        },
        'temperature': temperature,
        'maxOutputTokens': max_output_tokens
    }
    resp = requests.post(GEMINI_BASE, params=params, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()

def generate_questions(job_desc: str, resume_text: str) -> list:
    """
    Compose a prompt for question generation and return a list of 3 questions.
    The actual parsing of the Gemini response may need tweaking per model output format.
    """
    with open('prompts/prompt_generate_questions.txt','r') as f:
        base = f.read()
    prompt = f"""{base}\n\nJOB_DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}\n\nRespond with JSON only."""

    raw = call_gemini(prompt)
    # The response JSON structure from Gemini may be nested. Try to extract text.
    text = ''
    try:
        text = raw.get('candidates',[{}])[0].get('content', {}).get('text', '')
    except Exception:
        # Fallback: use raw string
        text = str(raw)
    # Attempt to parse JSON from the text
    try:
        parsed = json.loads(text)
        return parsed
    except Exception:
        # As fallback, return the raw text wrapped
        return [{ 'id': 'q1', 'question': text.strip(), 'area': 'general' }]

def score_answer(job_desc: str, resume_text: str, question: str, answer: str) -> Tuple[int,str]:
    """
    Compose a prompt for scoring a single answer and return (score, rationale).
    """
    with open('prompts/prompt_score_answer.txt','r') as f:
        base = f.read()
    prompt = f"""{base}\n\nJOB_DESCRIPTION:\n{job_desc}\n\nRESUME:\n{resume_text}\n\nQUESTION:\n{question}\n\nANSWER:\n{answer}\n\nRespond with JSON only."""

    raw = call_gemini(prompt)
    text = ''
    try:
        text = raw.get('candidates',[{}])[0].get('content', {}).get('text', '')
    except Exception:
        text = str(raw)
    try:
        parsed = json.loads(text)
        score = int(parsed.get('score', 0))
        rationale = parsed.get('rationale','')
        return score, rationale
    except Exception:
        # fallback: return 5 and the text
        return 5, text[:200]
