import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import APIError, RateLimitError

from ai import check_contract
from checklists import load_checklist
from extract import extract_docx, extract_pdf

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
CONTRACT_TYPES = {"employment", "lease", "business"}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/api/check")
async def check(contract_type: str = Form(...), file: UploadFile = File(...)):
    if contract_type not in CONTRACT_TYPES:
        raise HTTPException(400, "Please choose a contract type.")

    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        extractor = extract_pdf
    elif name.endswith(".docx"):
        extractor = extract_docx
    else:
        raise HTTPException(415, "Only PDF and DOCX files are supported.")

    data = await file.read(MAX_FILE_SIZE + 1)
    if not data:
        raise HTTPException(422, "The file is empty.")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "The file is too large. The limit is 10 MB.")

    try:
        blocks = extractor(data)
    except Exception:
        raise HTTPException(422, "Could not read this file. It may be damaged or password-protected.")

    if not blocks:
        raise HTTPException(422, "No text found. Scanned PDFs are not supported yet.")

    checklist = load_checklist(contract_type)

    try:
        result = await run_in_threadpool(check_contract, checklist, blocks)
    except RateLimitError:
        raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
    except (APIError, ValueError, json.JSONDecodeError):
        raise HTTPException(502, "The AI service failed. Please try again.")

    return {"contract_type": contract_type, "results": result.get("results", [])}