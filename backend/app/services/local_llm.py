from __future__ import annotations

import json
from urllib import error, request


class LocalLLMClient:
    def __init__(
        self,
        model: str = "qwen2.5:7b-instruct",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        try:
            req = request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )
            with request.urlopen(req, timeout=3) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(self, question: str, context: str) -> str:
        prompt = (
            "You are an AI educational tutor.\n\n"
            "Answer the student's question using ONLY the provided textbook context.\n\n"
            "If the textbook context does not contain enough information to answer the question, "
            "say that the information is not available in the provided material.\n\n"
            "Do not invent information.\n\n"
            "Explain concepts clearly and educationally.\n\n"
            "TEXTBOOK CONTEXT:\n"
            f"{context}\n\n"
            "QUESTION:\n"
            f"{question}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9},
        }

        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            # A local model can take longer than a minute on its first request.
            with request.urlopen(req, timeout=120) as response:
                body = response.read().decode("utf-8")
        except (error.URLError, TimeoutError, OSError):
            return ""

        try:
            result = json.loads(body)
            return (result.get("response") or "").strip()
        except json.JSONDecodeError:
            return ""
