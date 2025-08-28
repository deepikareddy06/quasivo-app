# Quasivo AI Challenge — Web App POC (Streamlit)

## Overview
A local Streamlit application that uses Google's Gemini API to automate first-round candidate screening.
This scaffold implements:
- Job Description (paste or upload)
- Candidate résumé (paste or upload PDF / text)
- Generates 3 custom interview questions via Gemini
- Lets candidate submit text answers
- Scores each answer (1-10) via Gemini
- Persists all JDs, résumés, questions, answers and scores locally to `./data/`

**Important:** The app does NOT include your Gemini API key. Create a `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
```
and **do not** commit the `.env` to a public repo.

## How to run (locally)
1. Create a Python 3.10+ virtualenv and activate it.
2. `pip install -r requirements.txt`
3. Create `.env` at project root with `GEMINI_API_KEY=...`
4. Run: `streamlit run app.py`

## Files / Structure
- `app.py` — main Streamlit app
- `utils.py` — helpers: PDF parsing, Gemini API wrapper functions
- `/prompts/` — example Gemini prompts used for generation & evaluation
- `/data/` — runtime output (created on demand) — contains JSON files of each session
- `requirements.txt` — Python deps
- `.gitignore` — ignore `.env`, `__pycache__`, and `/data/`

## Notes
- The app calls Gemini via simple HTTP `requests`. You can switch to the official SDK if preferred.
- PDF parsing uses PyPDF2 (works for most text PDFs). For scanned images you would need OCR (Tesseract).
- This scaffold keeps everything local per the challenge requirements.
