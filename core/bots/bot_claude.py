import json
import os
import time
from typing import Optional

import httpx
from github_action_utils import notice as info

from core.bots.bot import SYSTEM_MESSAGE, AiResponse, Bot, ModelOptions
from core.schemas.limits import TokenLimits
from core.schemas.options import Options


class ClaudeOptions(ModelOptions):
    """Options for Claude models hosted on Databricks."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        token_limits: Optional[TokenLimits] = None
    ):
        super().__init__(model, token_limits)


class ClaudeBot(Bot):
    """Bot implementation for Databricks-hosted Claude models (Opus and Sonnet)."""

    def __init__(
        self,
        options: Options,
        claude_options: ClaudeOptions,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        super().__init__(options, claude_options)

        if api_key is None:
            api_key = os.getenv("DATABRICKS_TOKEN") or os.getenv("CLAUDE_API_KEY")

        if base_url is None:
            base_url = os.getenv("DATABRICKS_BASE_URL")

        if not api_key:
            raise ValueError(
                "Unable to initialize the Claude API. "
                "Please provide api_key or set DATABRICKS_TOKEN or CLAUDE_API_KEY environment variable"
            )

        if not base_url:
            raise ValueError(
                "Unable to initialize the Claude API. "
                "Please provide base_url or set DATABRICKS_BASE_URL environment variable"
            )

        current_date = time.strftime("%Y-%m-%d")
        system_message = SYSTEM_MESSAGE.format(
            system_message=options.system_message,
            knowledge_cut_off=claude_options.token_limits.knowledge_cut_off,
            current_date=current_date,
            language=options.language,
        )

        self.api = {
            "system_message": system_message,
            "api_key": api_key,
            "base_url": base_url.rstrip('/'),  # Remove trailing slash
            "debug": options.debug,
            "max_model_tokens": claude_options.token_limits.max_tokens,
            "max_response_tokens": claude_options.token_limits.response_tokens,
            "temperature": options.model_temperature,
            "model": claude_options.model,
        }

        # Initialize httpx client for Databricks
        # Databricks uses Bearer token authentication
        self.client = httpx.Client(
            base_url=self.api["base_url"],
            headers={
                "Authorization": f"Bearer {self.api['api_key']}",
                "Content-Type": "application/json"
            },
            timeout=180.0
        )

        info(f"Initialized Claude bot with model: {claude_options.model}")
        info(f"Using Databricks endpoint: {base_url}")

    def chat(self, message: str) -> AiResponse:
        """Send a message to Claude via Databricks serving endpoint."""
        start = time.time()

        if not message:
            return AiResponse()

        response = None
        response_text = ""

        try:
            if self.options.debug:
                info(f"Sending message to Claude ({self.api['model']})")
                info(f"Message length: {len(message)} characters")
                # Log the full prompt for debugging
                info(f"[DEBUG] Full prompt being sent to Claude:")
                info(f"--- PROMPT START ---")
                info(message[:5000] + "..." if len(message) > 5000 else message)
                info(f"--- PROMPT END (showing first 5000 chars) ---")

            # Construct the request payload for Databricks serving endpoint
            # Databricks expects the Anthropic Messages API format
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "max_tokens": self.api["max_response_tokens"],
                "temperature": self.api["temperature"],
                "system": self.api["system_message"]
            }

            # Databricks serving endpoint URL format: {base_url}/{model_name}/invocations
            url = f"{self.api['base_url']}/{self.api['model']}/invocations"

            if self.options.debug:
                info(f"Request URL: {url}")

            # Make the request
            http_response = self.client.post(
                url,
                json=payload
            )

            # Check for errors
            http_response.raise_for_status()

            # Parse response
            response_json = http_response.json()

            if self.options.debug:
                info(f"Response status: {http_response.status_code}")

            # Extract the text from the response
            # Databricks returns OpenAI-compatible format: choices[0].message.content
            if "choices" in response_json and len(response_json["choices"]) > 0:
                message = response_json["choices"][0].get("message", {})
                response_text = message.get("content", "")

                if self.options.debug:
                    info(f"Claude response length: {len(response_text)} characters")
                    if "usage" in response_json:
                        info(f"Prompt tokens: {response_json['usage'].get('prompt_tokens', 0)}")
                        info(f"Completion tokens: {response_json['usage'].get('completion_tokens', 0)}")
                        info(f"Total tokens: {response_json['usage'].get('total_tokens', 0)}")
            else:
                info("Claude API returned empty content")

        except httpx.HTTPStatusError as e:
            info(f"Failed to send message to Claude API: HTTP {e.response.status_code}")
            info(f"Error details: {e.response.text}")
            return AiResponse(message="")

        except Exception as e:
            info(f"Failed to send message to Claude API: {e}")
            info(f"Error details: {str(e)}")
            return AiResponse(message="")

        end = time.time()
        elapsed_ms = (end - start) * 1000

        info(f"Claude API response time: {elapsed_ms:.2f} ms")

        # Clean up response text (remove common prefixes)
        if response_text.startswith("with "):
            response_text = response_text[5:]

        if self.options.debug:
            info(f"[DEBUG] Full Claude response:")
            info(f"--- RESPONSE START ---")
            info(response_text[:3000] + "..." if len(response_text) > 3000 else response_text)
            info(f"--- RESPONSE END (showing first 3000 chars) ---")

        return AiResponse(message=response_text)
