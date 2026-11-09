import logging
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from schemas import CheckResult

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
MAX_ATTEMPTS = 3
TIMEOUT_SECONDS = 90
MAX_OUTPUT_TOKENS = 8000

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=TIMEOUT_SECONDS,
    max_retries=0,
)

SYSTEM_PROMPT = """You review contracts for foreigners in China.
You receive a checklist and the contract text, split into numbered blocks.
For each checklist item, decide whether the contract covers it.
Answer only with json in exactly this shape:
{
  "results": [
    {
      "item_id": "probation",
      "found": true,
      "risk": "High",
      "explanation": "Risk assessment in one or two sentences.",
      "plain_language": "What the quoted clauses say, in simple words.",
      "quotes": [
        {"text": "Exact text copied from the contract.", "location": {"kind": "paragraph", "number": 3}}
      ]
    }
  ]
}
Rules:
- Return exactly one result per checklist item, in the same order.
- risk is "Low", "Medium" or "High".
- explanation is your risk assessment: why this risk level fits.
- plain_language says only what the quoted clauses say, in at most 2 short sentences. No legal opinion or advice.
- If found is true, give 1 to 3 quotes that support the finding.
- Copy each quote character for character from the contract, at least one full clause. Do not translate, summarize or correct it.
- If you must leave out text inside a quote, write …… in its place.
- If found is false, quotes must be [] and plain_language must be null.
- Write explanation and plain_language in LANGUAGE. Keep quotes in the original language."""


class AIOutputError(Exception):
    """The AI did not return valid results after all attempts."""


def format_blocks(blocks: list[dict]) -> str:
    parts = [f"[{block['kind']} {block['number']}]\n{block['text']}" for block in blocks]
    return "\n\n".join(parts)


def parse_result(content: str | None, item_ids: list[str]) -> CheckResult:
    if not content or not content.strip():
        raise ValueError("The answer was empty.")
    result = CheckResult.model_validate_json(content)
    returned = sorted(finding.item_id for finding in result.results)
    if returned != sorted(item_ids):
        raise ValueError("Return exactly one result for each item_id: " + ", ".join(item_ids))
    return result


def describe_error(error: ValueError) -> str:
    if isinstance(error, ValidationError):
        problems = error.errors(include_input=False, include_url=False)
        return "; ".join(
            ".".join(str(part) for part in problem["loc"]) + ": " + problem["msg"]
            for problem in problems
        )
    return str(error)


def check_contract(checklist: dict, blocks: list[dict], language: str = "English") -> CheckResult:
    item_ids = [item["id"] for item in checklist["items"]]
    items = "\n".join(f"- {item['id']}: {item['question']}" for item in checklist["items"])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("LANGUAGE", language)},
        {"role": "user", "content": f"CHECKLIST:\n{items}\n\nCONTRACT:\n{format_blocks(blocks)}"},
    ]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=MAX_OUTPUT_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
            temperature=0,
        )
        choice = response.choices[0]
        if choice.finish_reason != "stop":
            logger.warning("AI stopped early: %s", choice.finish_reason)
            raise AIOutputError()
        content = choice.message.content
        try:
            return parse_result(content, item_ids)
        except ValueError as error:
            logger.warning("Invalid AI output (attempt %d of %d): %s", attempt, MAX_ATTEMPTS, type(error).__name__)
            messages.append({"role": "assistant", "content": content or ""})
            messages.append({
                "role": "user",
                "content": f"Your json was invalid: {describe_error(error)}. Reply with the complete corrected json.",
            })

    raise AIOutputError()