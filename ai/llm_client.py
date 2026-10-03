import os
import json
import logging
import httpx
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    """
    Unified LLM API wrapper supporting structured JSON schema enforcement,
    multi-attempt self-correction retries, and offline mock generation mode.
    """
    def __init__(self, use_mock: Optional[bool] = None):
        if use_mock is not None:
            self.use_mock = use_mock
        else:
            mock_env = os.getenv("USE_MOCK_AI", "true").lower()
            self.use_mock = mock_env in ("true", "1", "yes")

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        mock_fallback: Optional[T] = None,
        max_retries: int = 2
    ) -> T:
        """
        Generates structured JSON output from LLM, validating against response_model schema.
        Automatically retries with schema error feedback if JSON/Pydantic validation fails.
        """
        is_mock_key = (
            self.openai_api_key.startswith("mock_") or
            self.gemini_api_key.startswith("mock_") or
            (not self.openai_api_key and not self.gemini_api_key)
        )

        if self.use_mock or is_mock_key:
            logger.info(f"[LLMClient] Mock provider active for model: {response_model.__name__}")
            if mock_fallback:
                return mock_fallback
            raise ValueError(f"No mock fallback provided for schema {response_model.__name__}")

        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        base_system_prompt = (
            f"{system_prompt}\n\n"
            f"CRITICAL REQUIREMENT: Respond ONLY with a raw, valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any text, notes, or explanations outside the JSON object."
        )

        current_user_prompt = user_prompt
        last_error = ""

        for attempt in range(max_retries + 1):
            if attempt > 0:
                current_user_prompt = (
                    f"{user_prompt}\n\n"
                    f"PREVIOUS ATTEMPT FAILED VALIDATION:\n"
                    f"Error details: {last_error}\n"
                    f"Fix the JSON formatting and field names to strictly match the requested schema."
                )
                logger.warning(f"[LLMClient] Retry attempt {attempt}/{max_retries} for {response_model.__name__}")

            try:
                raw_response = await self._call_llm_api(base_system_prompt, current_user_prompt)
                cleaned_text = self._extract_json_string(raw_response)
                parsed_json = json.loads(cleaned_text)
                return response_model.model_validate(parsed_json)
            except (json.JSONDecodeError, ValidationError, Exception) as err:
                last_error = str(err)
                logger.warning(f"[LLMClient] Schema validation failed on attempt {attempt}: {err}")

        logger.error(f"[LLMClient] All {max_retries + 1} LLM attempts failed. Reverting to mock fallback.")
        if mock_fallback:
            return mock_fallback
        raise ValueError(f"Failed to generate valid {response_model.__name__} after {max_retries + 1} retries: {last_error}")

    async def _call_llm_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        Dispatches HTTP request to OpenAI Chat Completions or Google Gemini API.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            if self.openai_api_key and not self.openai_api_key.startswith("mock_"):
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

            elif self.gemini_api_key and not self.gemini_api_key.startswith("mock_"):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": f"{system_prompt}\n\nUser Prompt: {user_prompt}"}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.7
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            else:
                raise ValueError("No valid LLM API key configured for OpenAI or Gemini.")

    def _extract_json_string(self, raw_text: str) -> str:
        """
        Extracts raw JSON block if enclosed in markdown code fences.
        """
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
