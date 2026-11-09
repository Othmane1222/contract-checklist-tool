from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from extract import extract_docx, extract_pdf

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
CONTRACT_TYPES = {"employment", "lease", "business"}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/api/extract")
async def extract(contract_type: str = Form(...), file: UploadFile = File(...)):
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

    return {"contract_type": contract_type, "blocks": blocks}