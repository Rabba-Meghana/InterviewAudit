import os
import time
from typing import List, Dict

from groq import Groq


class GroqChat:
    def __init__(self, model: str, temperature: float = 0.3, min_delay: float = 2.2):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Export it before running the evaluation.")
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.min_delay = min_delay
        self._last_call = 0.0

    def complete(self, messages: List[Dict[str, str]], max_tokens: int = 700, json_mode: bool = False) -> str:
        elapsed = time.time() - self._last_call
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)

        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._last_call = time.time()
        return response.choices[0].message.content.strip()

