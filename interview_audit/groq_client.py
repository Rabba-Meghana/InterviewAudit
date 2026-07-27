import os
import time
from typing import List, Dict

from groq import APIConnectionError, APIStatusError, Groq, RateLimitError


class GroqChat:
    def __init__(self, model: str, temperature: float = 0.3, min_delay: float = 2.2, max_retries: int = 6):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Export it before running the evaluation.")
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.min_delay = min_delay
        self.max_retries = max_retries
        self._last_call = 0.0

    def complete(self, messages: List[Dict[str, str]], max_tokens: int = 700, json_mode: bool = False) -> str:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(self.max_retries + 1):
            elapsed = time.time() - self._last_call
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                self._last_call = time.time()
                return response.choices[0].message.content.strip()
            except RateLimitError as exc:
                self._last_call = time.time()
                self._sleep_before_retry(attempt, exc, "rate limited/429")
            except APIConnectionError as exc:
                self._last_call = time.time()
                self._sleep_before_retry(attempt, exc, "connection error")
            except APIStatusError as exc:
                self._last_call = time.time()
                if exc.status_code in {500, 502, 503, 504}:
                    self._sleep_before_retry(attempt, exc, f"server error/{exc.status_code}")
                else:
                    raise

        raise RuntimeError(f"Groq request failed after {self.max_retries} retries for model {self.model}.")

    def _sleep_before_retry(self, attempt: int, exc: Exception, label: str) -> None:
        if attempt >= self.max_retries:
            raise exc
        retry_after = getattr(getattr(exc, "response", None), "headers", {}).get("retry-after")
        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = 0
        else:
            delay = min(60, 2 ** attempt * 4)
        print(f"[{self.model}] {label}; backing off {delay:.1f}s before retry {attempt + 1}/{self.max_retries}", flush=True)
        time.sleep(delay)
