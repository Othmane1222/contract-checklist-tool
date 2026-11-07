# Contract Checklist Tool: Project Notes

## Who I am
I am a beginner learning Python, JavaScript, VS Code, the terminal, Git and AI APIs. I am also a lawyer. My goals are to learn by doing the work myself and to finish a project good enough for my CV and GitHub.

## Most important rule: I write the code
- Do NOT create, edit or delete files in this project. Do NOT run commands for me.
- Give me code in the chat, one file or small piece at a time.
- Tell me exactly which folder and file to use, what to paste and where, what command to type, and what output to expect.
- After I paste the code, you may READ my files to check my work. I fix mistakes myself.
- When I get an error: first explain what it means and where to look, then give a hint. Give the full fix only if I ask.
- Every few steps, ask me one short question to check I understood.

## How we work
- Work in small milestones. Before each one, give a short plan: files, their purpose, and new concepts.
- Teach one or two VS Code skills per milestone, with Windows and Mac shortcuts.
- Explain every new term in plain language the first time it appears.
- End each milestone with a glossary, a recap, how to run it, and Git commit steps. Wait for me to confirm before moving on.
- I make the Git commits myself.
- If a choice is ambiguous, propose 2 options with a recommendation, then wait for me to choose.

## Stack
- Backend: Python + FastAPI, run with Uvicorn
- Frontend: simple HTML, CSS and JavaScript
- Validation: Pydantic
- AI API: DeepSeek proposed, to be confirmed in Milestone 3
- Hosting: to be decided in Milestone 8

## How to run
    .venv\Scripts\Activate.ps1
    python -m uvicorn main:app --reload
Then open http://127.0.0.1:8000

## Project rules
- I am based in mainland China. Recommend services I can access from here and say where a VPN is needed.
- Use a cheap AI model during development and a stronger one only for final testing.
- API keys go in a .env file that is never committed to Git.
- Process files in memory. Never store uploaded contracts or log contract text.
- Show this disclaimer on the page: "This is an automated checklist, not legal advice."
- No secrets or contract data in the repo.

## Conventions
- The 10 checklist items live in a config file.
- Every finding quotes the exact source clause and its location. Flag or reject quotes not found in the document.
- Location means page number for PDFs and paragraph number for Word files.

## Milestones
1. Setup and hello world (in progress)
2. Upload page and text extraction
3. AI call with checklist prompt and JSON schema
4. Validation, retry and source-quote verification
5. Results table, CSV download, error messages, disclaimer
6. English, Spanish and Chinese
7. Evaluation script, test set and accuracy report
8. Privacy check, tests, README screenshots, deployment
9. Design decisions and limitations write-up
10. Stretch goals: chunking, OCR, PDF export