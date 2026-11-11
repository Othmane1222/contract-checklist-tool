import logging
import os
import smtplib

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from ai import AIOutputError, check_contract
from checklists import CONTRACT_TYPES, LANGUAGES, load_checklist
from errors import AppError, error_body
from extract import extract_docx, extract_pdf
from mailer import send_contact_email
from ratelimit import RateLimiter
from schemas import ContactRequest
from verify import verify_findings

logger = logging.getLogger(__name__)

MAX_FILE_MB = 10
MAX_FILE_SIZE = MAX_FILE_MB * 1024 * 1024
AI_LANGUAGES = {"en": "English", "es": "Spanish", "zh": "Simplified Chinese"}
# In-memory limit: requires a single server worker (uvicorn --workers 1).
CONTACT_LIMIT = RateLimiter(max_requests=3, window_seconds=600)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(AppError)
async def handle_app_error(request: Request, error: AppError):
    return JSONResponse(error_body(error.code, **error.params), status_code=error.status_code)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, error: RequestValidationError):
    code = "contact_invalid" if request.url.path == "/api/contact" else "invalid_request"
    return JSONResponse(error_body(code), status_code=422)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    length = request.headers.get("content-length", "")
    if request.url.path == "/api/check" and length.isdigit() and int(length) > MAX_FILE_SIZE + 1024 * 1024:
        return JSONResponse(error_body("file_too_large", max_mb=MAX_FILE_MB), status_code=413)
    return await call_next(request)


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/check")
def check_page():
    return FileResponse("static/check.html")


@app.post("/api/check")
async def check(
    contract_type: str = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(...),
):
    if contract_type not in CONTRACT_TYPES:
        raise AppError(400, "invalid_contract_type")
    if language not in LANGUAGES:
        raise AppError(400, "invalid_language")

    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        extractor = extract_pdf
    elif name.endswith(".docx"):
        extractor = extract_docx
    else:
        raise AppError(415, "unsupported_file_type")

    data = await file.read(MAX_FILE_SIZE + 1)
    if not data:
        raise AppError(422, "file_empty")
    if len(data) > MAX_FILE_SIZE:
        raise AppError(413, "file_too_large", max_mb=MAX_FILE_MB)

    try:
        blocks = extractor(data)
    except Exception:
        raise AppError(422, "file_unreadable")

    if not blocks:
        raise AppError(422, "no_text_found")

    checklist = load_checklist(contract_type)

    try:
        result = await run_in_threadpool(check_contract, checklist, blocks, AI_LANGUAGES[language])
    except RateLimitError:
        raise AppError(429, "ai_rate_limited")
    except APITimeoutError:
        raise AppError(504, "ai_timeout")
    except APIConnectionError:
        raise AppError(502, "ai_unreachable")
    except (APIError, AIOutputError) as error:
        logger.warning("AI check failed: %s", type(error).__name__)
        raise AppError(502, "ai_failed")

    findings, stats = verify_findings(result, blocks, checklist, language)
    return {"contract_type": contract_type, "language": language, "results": findings, "stats": stats}


@app.post("/api/contact")
async def contact(request: Request, form: ContactRequest):
    if form.website:
        return {"ok": True}  # honeypot filled: pretend success, send nothing

    client_ip = request.client.host if request.client else "unknown"
    if not CONTACT_LIMIT.allow(client_ip):
        raise AppError(429, "contact_rate_limited")

    try:
        await run_in_threadpool(send_contact_email, form)
    except (smtplib.SMTPException, OSError) as error:
        logger.warning("Contact email failed: %s", type(error).__name__)
        fallback = os.getenv("CONTACT_FALLBACK_EMAIL", "")
        if fallback:
            raise AppError(502, "contact_send_failed", email=fallback)
        raise AppError(502, "contact_send_failed_no_fallback")

    return {"ok": True}