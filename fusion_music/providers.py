from __future__ import annotations

import abc
import json
import urllib.request


class PlanProvider(abc.ABC):
    name = "provider"

    @abc.abstractmethod
    def generate(self, prompt: str, seed: int) -> str:
        raise NotImplementedError


class OllamaPlanProvider(PlanProvider):
    name = "ollama"

    def __init__(
        self,
        model: str = "phi4-mini",
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 90,
        temperature: float = 0.95,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def generate(self, prompt: str, seed: int) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "seed": seed,
            },
        }
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data["response"]


def create_provider(
    name: str,
    model: str = "phi4-mini",
    host: str = "http://127.0.0.1:11434",
    timeout_seconds: int = 90,
    temperature: float = 0.95,
) -> PlanProvider:
    normalized = name.strip().lower()
    if normalized == "ollama":
        return OllamaPlanProvider(
            model=model,
            host=host,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
        )
    raise ValueError(f"Unsupported provider: {name}")
