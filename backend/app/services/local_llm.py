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
            "You are a retrieval-grounded educational tutor.\n\n"
            "Your response must be supported entirely by TEXTBOOK CONTEXT.\n"
            "If the context does not directly answer the question, respond with exactly: "
            "INSUFFICIENT_CONTEXT\n\n"
            "Otherwise, act like a helpful tutor explaining the slides to a student. Give a "
            "clear 2-4 sentence answer in your own words: define the idea, explain how the "
            "slide's points fit together, and use a brief example only if the context supports "
            "it. Do NOT quote, copy, or closely mirror the wording or bullet structure of the "
            "context. Do not use outside knowledge or add unsupported claims. Do not add page "
            "citations; the application adds them.\n\n"
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

    def generate_quiz(self, context: str, topic: str | None = None) -> str:
        topic_instruction = f"Focus on: {topic}." if topic else "Choose the most teachable definition or concept."
        prompt = (
            "You create one multiple-choice quiz question using ONLY the TEXTBOOK CONTEXT below. "
            "Do not use outside knowledge. The correct answer and explanation must be directly supported by the context. "
            "Create three plausible but clearly incorrect distractors. "
            f"{topic_instruction}\n\n"
            "Return valid JSON only, with this exact shape:\n"
            '{"question":"...","options":["...","...","...","..."],"correct_option":0,"explanation":"..."}\n\n'
            "TEXTBOOK CONTEXT:\n"
            f"{context}"
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "top_p": 0.9},
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=120) as response:
                body = response.read().decode("utf-8")
            return (json.loads(body).get("response") or "").strip()
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return ""

    def generate_flashcard(self, context: str, topic: str | None = None) -> str:
        topic_instruction = f"Focus on: {topic}." if topic else "Choose one important definition or concept."
        prompt = (
            "You create one study flashcard using ONLY the TEXTBOOK CONTEXT below. "
            "Do not use outside knowledge. The back must be fully supported by the context. "
            f"{topic_instruction}\n\n"
            "Return valid JSON only in this exact shape:\n"
            '{"front":"a concise question","back":"a concise textbook-grounded answer"}\n\n'
            "TEXTBOOK CONTEXT:\n"
            f"{context}"
        )
        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.1, "top_p": 0.9}}
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(f"{self.base_url}/api/generate", data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=120) as response:
                body = response.read().decode("utf-8")
            return (json.loads(body).get("response") or "").strip()
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return ""

    def generate_summary(self, context: str, topic: str) -> str:
        prompt = (
            "You create a clear, student-friendly chapter summary using ONLY the TEXTBOOK CONTEXT below. "
            "Do not use outside knowledge or invent information. Return 4 to 8 concise points that cover the important ideas.\n\n"
            "Return valid JSON only in this exact shape:\n"
            '{"title":"Chapter summary title","points":["important idea 1","important idea 2"]}\n\n'
            f"CHAPTER OR TOPIC: {topic}\n\nTEXTBOOK CONTEXT:\n{context}"
        )
        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.15, "top_p": 0.9}}
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(f"{self.base_url}/api/generate", data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=120) as response:
                body = response.read().decode("utf-8")
            return (json.loads(body).get("response") or "").strip()
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return ""
