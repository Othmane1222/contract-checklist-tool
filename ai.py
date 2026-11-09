import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

SYSTEM_PROMPT = """You review contracts for foreigners in China.
You receive a checklist and the contract text, split into numbered blocks.
For each checklist item, decide whether the contract covers it.
Answer only with json in exactly this shape:
{
  "results": [
    {
      "item_id": "contract_term",
      "found": true,
      "risk": "Low",
      "explanation": "One or two sentences.",
      "quote": "Exact text copied from the contract.",
      "location": {"kind": "paragraph", "number": 3}
    }
  ]
}
Rules:
- Return one result per checklist item, in the same order.
- risk is "Low", "Medium" or "High".
- Copy the quote character for character from one block. Do not translate or shorten it.
- If an item is not found, set quote to "" and location to null.
- Write explanations in LANGUAGE. Keep quotes in the original language."""


def format_blocks(blocks: list[dict]) -> str:
    parts = [f"[{block['kind']} {block['number']}]\n{block['text']}" for block in blocks]
    return "\n\n".join(parts)


def check_contract(checklist: dict, blocks: list[dict], language: str = "English") -> dict:
    items = "\n".join(f"- {item['id']}: {item['question']}" for item in checklist["items"])
    user_message = f"CHECKLIST:\n{items}\n\nCONTRACT:\n{format_blocks(blocks)}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.replace("LANGUAGE", language)},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        max_tokens=4000,
    )

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("Empty response from the AI")
    return json.loads(content)