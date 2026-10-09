import json
from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


class GeminiCallResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    data: dict
    model: str
    tokens: int | None


async def generate_structured(
    *, system_prompt: str, user_prompt: str, response_schema: type[BaseModel]
) -> GeminiCallResult:
    """Calls Gemini with a forced JSON response shape, validated against
    `response_schema`. Raises on any failure — missing key, API error,
    malformed JSON, schema mismatch — so callers can apply one retry/fallback
    policy instead of branching on failure type."""
    client = get_gemini_client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    settings = get_settings()
    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )

    data = json.loads(response.text)
    response_schema.model_validate(data)  # raises if the shape doesn't match

    tokens = response.usage_metadata.total_token_count if response.usage_metadata else None
    return GeminiCallResult(data=data, model=settings.gemini_model, tokens=tokens)
