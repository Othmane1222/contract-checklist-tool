# Contract Checklist Tool: Project Notes

## Working rules
- I write all the code myself. Do not create, edit or delete files, and do not run commands, unless I explicitly ask.
- For each milestone, give a numbered step plan (Step 1, Step 2...). Each step names the file to create or change, the code to paste, and the command to run, if any.
- Keep it short: one line on what each step does. No tutorials or glossaries unless I ask.
- You may read my files to check my work. When something breaks, give the cause and the fix briefly.
- Tell me when to commit and suggest a commit message. I make the commits.
- If a choice is ambiguous, propose 2 options with a recommendation and wait for me to choose.

## Skills
- superpowers: use brainstorming and writing-plans to shape each milestone and its step plan, and systematic-debugging when I hit errors. Do not use executing-plans or subagent-driven-development.
- frontend-design: use it in the design milestone.

## Product
A personal project, independent of any firm: a web tool that helps foreigners in China understand contracts written in Chinese. Built to CV standard and to be presentable to law firms as a product they could adopt. No firm names or branding anywhere.

## Features
Phase 1
1. Contract type selection: Employment contract, Apartment lease, Business agreement. Each type has its own checklist in a config file. I write the items; use placeholders until then.
2. Results table: Checklist item | Found? | Risk (Low/Medium/High) | Short explanation | Source quote with location (page for PDF, paragraph for DOCX). Validate AI output against a schema, retry if invalid, and reject any finding whose quote is not in the document.
3. "Explain it to me" mode: the original Chinese clause side by side with a plain-language explanation in the user's language.
4. "Get help from a lawyer" contact form on the results page, highlighted when any item is High risk. Sends name, contact, contract type and a short description to a recipient email set in .env, so a firm can plug in its own address. Never attaches the contract.

Phase 2
5. Know-your-rights guides in Markdown files (renting, employment, visas and work permits, opening a company), linked from matching results.
6. Deadline extraction (end date, renewal notice, payment dates) with an .ics calendar download.

## Requirements
- Languages: UI and results in English, Spanish and Chinese. Contracts are mostly Chinese, sometimes bilingual.
- Privacy: process files in memory, never store contracts, never log contract text.
- Disclaimer on every results page, in all three languages: "This is an automated checklist, not legal advice."
- Clear error messages: unsupported file type, file too large, empty or unreadable file, AI API failure, rate limiting.
- Secrets (API keys, email settings) only in .env, never committed.
- Evaluation test set with an accuracy report, automated tests for parsing and validation, and a live deployment.
- I am in mainland China: choose an AI API and hosting reachable from here, and say where a VPN is needed. Cheap model in development, stronger model for final testing.
- Design: plain, neutral layout for now. All styling lives in static/style.css using CSS variables, so it is easy to restyle.

## Stack
- Backend: Python 3.14, FastAPI, Uvicorn
- Frontend: HTML, CSS and plain JavaScript in static/
- Validation: Pydantic
- AI API: DeepSeek (confirmed)
- Contact form email: SMTP via a dedicated 163 mailbox (fallback: Tencent Cloud SES over HTTPS)
- Hosting: to be decided in Milestone 10 (AWS Free plan account available, Sydney only for now)

## How to run (Windows)
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python -m uvicorn main:app --reload
Then open http://127.0.0.1:8000

## Milestones
1. Setup and hello world (done)
2. Contract type selection, upload page, text extraction with locations
3. Checklist config files and AI call returning JSON
4. Schema validation, retry and source-quote check
5. Results table and error messages
6. "Explain it to me" mode
7. Contact form
8. Languages: English, Spanish, Chinese
9. Design (frontend-design), including a "Save as PDF / Print" button with print-friendly CSS, and cards instead of table rows on small screens
10. Evaluation set and accuracy report (run each contract at least twice to measure variation), tests, privacy check, deployment with a security checklist (HTTPS, firewall, process manager, automatic updates, SSH keys, a single uvicorn worker for the in-memory rate limit, and an SMTP send test from the server)
11. Design decisions and limitations write-up
12. Phase 2: know-your-rights guides
13. Phase 2: deadline extraction and .ics download
Stretch: OCR for scanned PDFs, chunking for long contracts.
Later: expand beyond a single checker into a fuller product (scope to be brainstormed)