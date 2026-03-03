from __future__ import annotations

import os
import time
from typing import Optional

import httpx
from github_action_utils import notice as info

from core.bots.bot import SYSTEM_MESSAGE, AiResponse, Bot, ModelOptions
from core.schemas.limits import TokenLimits
from core.schemas.options import Options


class LocalOptions(ModelOptions):
    """Options for local Ollama models."""

    def __init__(self, model: str, token_limits: Optional[TokenLimits] = None):
        super().__init__(model, token_limits)


class LocalBot(Bot):
    """
    Bot implementation for local Ollama (http://localhost:11434 by default).
    Uses Ollama /api/generate with stream=False.
    """

    def __init__(
        self,
        options: Options,
        local_options: LocalOptions,
        base_url: str | None = None,
    ):
        super().__init__(options, local_options)

        # Allow config via env or options
        if base_url is None:
            base_url = (
                getattr(options, "local_base_url", None)
                or os.getenv("LOCAL_BASE_URL")
                or os.getenv("OLLAMA_BASE_URL")
                or "http://localhost:11434"
            )

        self.base_url = base_url.rstrip("/")
        self.model = local_options.model

        current_date = time.strftime("%Y-%m-%d")
        self.system_message = SYSTEM_MESSAGE.format(
            system_message=options.system_message,
            knowledge_cut_off=local_options.token_limits.knowledge_cut_off,
            current_date=current_date,
            language=options.language,
        )

        # httpx client
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Content-Type": "application/json"},
            timeout=max(30.0, float(options.timeout_ms) / 1000.0) if options.timeout_ms else 180.0,
        )

        # PR context (optional; used only if you later add observability)
        self.pr_context = {
            "pr_number": None,
            "repository": os.getenv("GITHUB_REPOSITORY", "unknown"),
        }

        info(f"Initialized LocalBot with model: {self.model}")
        info(f"Ollama base URL: {self.base_url}")

    def set_pr_context(self, pr_number: int, repository: str = None):
        self.pr_context["pr_number"] = pr_number
        if repository:
            self.pr_context["repository"] = repository

    def chat(
        self,
        message: str,
        files_reviewed: int = None,
        comments_generated: int = None,
        lines_of_code_reviewed: int = None,
    ) -> AiResponse:
        if not message:
            return AiResponse(message="")

        start = time.time()

        # We inject the repo's SYSTEM message + the user prompt into a single prompt,
        # because /api/generate is prompt-based (not messages-based).
        prompt = f"{self.system_message}\n\n{message}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # optional knobs (Ollama supports some; safe if ignored by model)
            "options": {
                "temperature": float(self.options.model_temperature or 0.0),
            },
        }

        try:
            if self.options.debug:
                info(f"[LocalBot] POST {self.base_url}/api/generate model={self.model}")
                info(f"[LocalBot] Prompt chars: {len(prompt)}")

            r = self.client.post("/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()

            # Ollama returns: {"response": "...", ...}
            text = (data.get("response") or "").strip()

            elapsed_ms = (time.time() - start) * 1000
            info(f"Local/Ollama response time: {elapsed_ms:.2f} ms")

            if self.options.debug:
                info(f"[LocalBot] Response chars: {len(text)}")

            return AiResponse(message=text)

        except Exception as e:
            if self.options.debug:
                info(f"[LocalBot] Failed: {e}")
            return AiResponse(message="")
