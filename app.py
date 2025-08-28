import streamlit as st
import os, json, datetime
from utils import extract_text_from_pdf, generate_questions, score_answer

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title='Quasivo — Candidate Screen POC', layout='centered')
st.title('Quasivo — First-Round Candidate Screening (POC)')

st.sidebar.header('Inputs')
jd_input = st.sidebar.text_area('Paste Job Description (or upload file below)', height=200)
jd_file = st.sidebar.file_uploader('Upload Job Description (txt/markdown)', type=['txt','md'])
resume_text_input = st.sidebar.text_area('Paste résumé text (or upload PDF below)', height=200)
resume_file = st.sidebar.file_uploader('Upload Résumé (PDF or txt)', type=['pdf','txt'])

if jd_file is not None:
    jd_raw = jd_file.read().decode('utf-8', errors='ignore')
    jd_input = jd_input + '\n' + jd_raw

resume_text = resume_text_input
if resume_file is not None:
    if resume_file.type == 'application/pdf' or resume_file.name.lower().endswith('.pdf'):
        # save temporary
        tmp_path = os.path.join(DATA_DIR, 'tmp_resume.pdf')
        with open(tmp_path, 'wb') as f:
            f.write(resume_file.read())
        resume_text = extract_text_from_pdf(tmp_path)
    else:
        resume_text = resume_file.read().decode('utf-8', errors='ignore')

st.header('Preview')
st.subheader('Job Description')
st.code(jd_input[:1000] + ('...' if len(jd_input)>1000 else ''))
st.subheader('Résumé')
st.code(resume_text[:1000] + ('...' if len(resume_text)>1000 else ''))

if st.button('Generate 3 Interview Questions'):
    if not jd_input.strip() or not resume_text.strip():
        st.error('Please provide both a Job Description and a résumé (paste or upload).')
    else:
        with st.spinner('Calling Gemini to generate questions...'):
            try:
                questions = generate_questions(jd_input, resume_text)
            except Exception as e:
                st.error(f'Generation error: {e}')
                questions = []
        # Normalize questions list
        if isinstance(questions, dict):
            questions = [questions]
        if not isinstance(questions, list):
            questions = [{'id': 'q1', 'question': str(questions)}]

        st.session_state['questions'] = questions[:3]

if 'questions' in st.session_state:
    st.header('Interview Questions (candidate will answer below)')
    answers = {}
    for q in st.session_state['questions']:
        qid = q.get('id', f"q{len(answers)+1}")
        st.write(f"**{q.get('question')}**")
        ans = st.text_area(f'Answer for {qid}', key=f'ans_{qid}', height=120)
        answers[qid] = {'question': q.get('question'), 'answer': ans}

    if st.button('Score Answers'):
        results = []
        with st.spinner('Scoring with Gemini...'):
            for qid, qa in answers.items():
                try:
                    score, rationale = score_answer(jd_input, resume_text, qa['question'], qa['answer'])
                except Exception as e:
                    score, rationale = 0, f'Error scoring: {e}'
                results.append({'id': qid, 'question': qa['question'], 'answer': qa['answer'], 'score': score, 'rationale': rationale})

        # persist
        ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        out = {
            'timestamp': ts,
            'job_description': jd_input,
            'resume_text': resume_text,
            'results': results
        }
        fname = os.path.join(DATA_DIR, f'session_{ts}.json')
        with open(fname,'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        st.success('Scoring complete — results saved locally.')
        st.header('Summary')
        for r in results:
            st.subheader(f"{r['id']} — Score: {r['score']}")
            st.write('Question:')
            st.write(r['question'])
            st.write('Answer:')
            st.write(r['answer'] or '_No answer provided_')
            st.write('Rationale:')
            st.write(r['rationale'])
            st.write('---')
