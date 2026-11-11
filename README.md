# Contract Checklist Tool

A web tool that helps foreigners in China understand contracts written in Chinese. Upload an employment contract, apartment lease or business agreement (PDF or DOCX) and get a checklist of key terms, risk levels and plain-language explanations, each backed by an exact quote from the contract.

> This is an automated checklist, not legal advice.

**Status:** in development.

## Features

- Checklist results for each contract type: found or missing, risk level, short explanation, and the source quote with its page or paragraph
- Verified output: AI answers are checked against a schema, and any quote that does not appear in the contract is rejected
- "Explain it to me": the original Chinese clause next to a plain-language explanation
- "Get help from a lawyer" contact form (the contract itself is never sent)
- English, Spanish and Chinese

## Languages

The page and the results are available in English, Spanish and Simplified Chinese. The page follows the browser's language and remembers the user's choice. Browsers set to Traditional Chinese (zh-TW, zh-HK) are shown Simplified Chinese.

## Privacy

- The uploaded file is deleted from memory after processing. It is not written to disk or to logs on our server.
- The contract text is sent to the AI provider, DeepSeek, for analysis. DeepSeek's own privacy policy applies to that text.
- Messages sent to a lawyer never include the contract.
- The server will be hosted outside mainland China (to be confirmed at deployment).

## Run it locally (Windows)

```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env    # then fill in your own values
python -m uvicorn main:app --reload
```

Then open http://127.0.0.1:8000

## Tests

```
python -m pytest
```