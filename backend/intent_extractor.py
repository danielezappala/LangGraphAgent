"""
LLM-based intent extractor (zero-/few-shot).
Restituisce un dict {"intent": ..., "entities": ...}.
"""
from __future__ import annotations
import json
from typing import List, Dict, Literal, TypedDict

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()               # legge OPENAI_API_KEY dal .env
client = OpenAI()

INTENTS = ["weather", "agenda", "food", "joke", "general", "unknown"]

class IntentResult(TypedDict):
    intent: Literal["weather", "agenda", "food", "joke", "general", "unknown"]
    entities: Dict | List

# ---------- (facoltativo) esempi few-shot ------------------------------
FEW_SHOTS: list[dict] = [
    # 1️⃣ Meteo
    {"role": "user",      "content": "Che tempo fa a Roma domani?"},
    {"role": "assistant", "content": json.dumps(
        {"intent": "weather", "entities": {"city": "Roma", "date": "domani"}},
        ensure_ascii=False)},
    # 2️⃣ Cibo
    {"role": "user",      "content": "Che si mangia oggi?"},
    {"role": "assistant", "content": json.dumps(
        {"intent": "food", "entities": {}}, ensure_ascii=False)},
]
# ----------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an intent-extraction function. "
    f"Classify the user request into exactly one of: {INTENTS}. "
    "Extract simple entities like city or date when relevant. "
    "Return ONLY valid JSON with keys 'intent' and 'entities' – no extra text."
)

def extract_intent(text: str) -> IntentResult:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += FEW_SHOTS                    # ⇦ rimuovi se vuoi puro zero-shot
    messages.append({"role": "user", "content": text})

    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0, messages=messages
    )
    raw = resp.choices[0].message.content
    try:
        data = json.loads(raw)
        intent = data.get("intent", "unknown")
        if intent not in INTENTS:
            intent = "unknown"
        return {"intent": intent, "entities": data.get("entities", {})}
    except Exception:
        return {"intent": "unknown", "entities": {}}
