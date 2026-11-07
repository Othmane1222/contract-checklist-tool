# Contract Checklist Tool

A website that checks a contract (PDF or Word) against a 10-item legal checklist and shows the results in a table.

> This is an automated checklist, not legal advice.

**Status:** in development. Currently a "hello world" page.

## How to run it locally

1. Create and activate a virtual environment:

   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install the packages:

   ```
   python -m pip install -r requirements.txt
   ```

3. Start the server:

   ```
   python -m uvicorn main:app --reload
   ```

4. Open http://127.0.0.1:8000 in your browser.