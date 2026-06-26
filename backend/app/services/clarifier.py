"""
Clarifier service — generates a friendly, structured message asking the user
for missing critical information before generating a full recommendation.
"""

import asyncio
import json
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

CLARIFICATION_SYSTEM_PROMPT = """
You are a helpful assistant inside an AI infrastructure advisor tool.

The user has submitted a use case, but critical information is missing.
You have been given a list of clarification questions to ask.

Your job: Ask the user these questions in a conversational, friendly way.
Group related questions together. Explain briefly WHY each piece of information
matters for the recommendation.

Keep it short — no more than the questions provided (max 3 total).
Do not ask questions that can be answered with "I don't know" — offer concrete options.

Format your message as markdown:
  - One short intro sentence
  - Numbered questions, each with a brief parenthetical explaining why it matters
  - A closing line telling the user they can answer any or all, and skip what they don't know

Return ONLY the message as plain markdown text. No JSON wrapper.
"""


async def generate_clarification_message(questions: list[str]) -> str:
    """
    Generate a friendly clarification message using Gemini.
    Falls back to a simple local formatter if API unavailable.
    """
    if not questions:
        return ""

    settings = get_settings()
    api_key = settings.GEMINI_API_KEY

    if not api_key or "gemini-key" in api_key or "your-key" in api_key:
        return _format_clarification_locally(questions)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    prompt = (
        f"Please format these clarification questions in a friendly, helpful way for the user:\n\n"
        + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": CLARIFICATION_SYSTEM_PROMPT}]},
        "generationConfig": {"responseMimeType": "text/plain"},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=12.0)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
            else:
                logger.warning("Gemini returned %s for clarifier, using local format.", response.status_code)
                return _format_clarification_locally(questions)
    except Exception as e:
        logger.warning("Error in clarifier API call: %s. Using local format.", e)
        return _format_clarification_locally(questions)


def _format_clarification_locally(questions: list[str]) -> str:
    """Local fallback formatter for clarification questions."""
    lines = [
        "To give you the most accurate recommendation, I need a few more details:\n"
    ]
    for i, q in enumerate(questions, 1):
        lines.append(f"**{i}.** {q}\n")
    lines.append(
        "\nAnswer any you know — skip the rest and I'll make reasonable assumptions for unknowns."
    )
    return "\n".join(lines)
