import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from checklists import LANGUAGES, label_for, load_checklist
from schemas import ContactRequest

load_dotenv()

SMTP_TIMEOUT_SECONDS = 10

EMAIL_TEXT = {
    "en": {
        "subject": "Contract checklist: help request",
        "name": "Name",
        "email": "Email",
        "contract_type": "Contract type",
        "user_language": "User's language",
        "message": "Message",
        "summary": "Checklist summary as reported by the user (no contract text):",
        "line": "- {label}: {status}, risk: {risk}",
        "statuses": {"quote_verified": "source found", "unverified": "unverified", "possibly_present": "possibly present", "not_found": "not found"},
        "risks": {"Low": "Low", "Medium": "Medium", "High": "High"},
        "contract_types": {"employment": "employment contract", "lease": "apartment lease", "business": "business agreement"},
        "languages": {"en": "English", "es": "Spanish", "zh": "Chinese"},
    },
    "es": {
        "subject": "Lista de verificación de contratos: solicitud de ayuda",
        "name": "Nombre",
        "email": "Correo electrónico",
        "contract_type": "Tipo de contrato",
        "user_language": "Idioma del usuario",
        "message": "Mensaje",
        "summary": "Resumen de la lista según lo informado por el usuario (sin texto del contrato):",
        "line": "- {label}: {status}, riesgo: {risk}",
        "statuses": {"quote_verified": "fuente encontrada", "unverified": "sin verificar", "possibly_present": "posiblemente presente", "not_found": "no encontrado"},
        "risks": {"Low": "Bajo", "Medium": "Medio", "High": "Alto"},
        "contract_types": {"employment": "contrato laboral", "lease": "contrato de arrendamiento", "business": "acuerdo comercial"},
        "languages": {"en": "inglés", "es": "español", "zh": "chino"},
    },
    "zh": {
        "subject": "合同检查清单：求助请求",
        "name": "姓名",
        "email": "电子邮箱",
        "contract_type": "合同类型",
        "user_language": "用户语言",
        "message": "留言",
        "summary": "用户提供的检查清单摘要（不含合同文本）：",
        "line": "- {label}：{status}，风险：{risk}",
        "statuses": {"quote_verified": "已找到原文", "unverified": "未核实", "possibly_present": "可能存在", "not_found": "未找到"},
        "risks": {"Low": "低", "Medium": "中", "High": "高"},
        "contract_types": {"employment": "劳动合同", "lease": "房屋租赁合同", "business": "商业合同"},
        "languages": {"en": "英语", "es": "西班牙语", "zh": "中文"},
    },
}


def contact_language() -> str:
    language = os.getenv("CONTACT_LANGUAGE", "en")
    return language if language in LANGUAGES else "en"


def build_message(request: ContactRequest, sender: str, recipient: str, language: str = "en") -> EmailMessage:
    text = EMAIL_TEXT[language]
    contract_type = text["contract_types"][request.contract_type]

    message = EmailMessage()
    message["Subject"] = f"{text['subject']} ({contract_type})"
    message["From"] = sender
    message["To"] = recipient
    message["Reply-To"] = str(request.email)

    lines = [
        f"{text['name']}: {request.name}",
        f"{text['email']}: {request.email}",
        f"{text['contract_type']}: {contract_type}",
        f"{text['user_language']}: {text['languages'][request.user_language]}",
        "",
        f"{text['message']}:",
        request.description,
    ]
    if request.summary:
        items = {item["id"]: item for item in load_checklist(request.contract_type)["items"]}
        lines += ["", text["summary"]]
        for entry in request.summary:
            lines.append(text["line"].format(
                label=label_for(items[entry.item_id], language),
                status=text["statuses"][entry.status],
                risk=text["risks"][entry.risk],
            ))
    message.set_content("\n".join(lines))
    return message


def send_contact_email(request: ContactRequest) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    message = build_message(request, sender=user, recipient=os.environ["CONTACT_RECIPIENT"], language=contact_language())

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.login(user, password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(message)