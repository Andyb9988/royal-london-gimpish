from __future__ import annotations

from google import genai

from app.core.config import settings
from app.schemas.extract_moments import ExtractMomentsOut

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def build_prompt(report_text: str) -> str:
    return (
        "Extract the following fields from this 5-a-side match report.\n"
        "- gimp_name: who is 'gimp of the day' (if explicitly implied)\n"
        "- champagne_moment: the best moment as a short excerpt\n\n"
        "Rules:\n"
        "- If a field is not present, return null for that field.\n"
        "- Output will be validated against the provided JSON schema.\n\n"
        f"REPORT:\n{report_text}\n"
    )


def extract_moments(report_text: str) -> ExtractMomentsOut:
    client = _get_client()
    prompt = build_prompt(report_text)
    response = client.models.generate_content(
        model=settings.GEMINI_EXTRACT_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": ExtractMomentsOut.model_json_schema(),
        },
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemini response was empty")
    return ExtractMomentsOut.model_validate_json(text)


__all__ = ["extract_moments", "build_prompt"]
