from __future__ import annotations

import os
import time
from typing import Optional

import httpx
from github_action_utils import notice as info

from core.bots.bot import SYSTEM_MESSAGE, AiResponse, Bot, ModelOptions
from core.schemas.limits import TokenLimits
from core.schemas.options import Options

# Import Langfuse for LLM observability
try:
    from langfuse import Langfuse
    from langfuse.types import TraceContext
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    info("Langfuse not installed. Install with: pip install langfuse")
    Langfuse = None
    TraceContext = None

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

        # Initialize Langfuse for observability (v3.14.5 API)
        self.langfuse = None
        langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

        if LANGFUSE_AVAILABLE and langfuse_enabled:
            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

            if langfuse_public_key and langfuse_secret_key:
                try:
                    # Initialize Langfuse for LLM observability
                    # flush_at=1: Flush after each observation (prevents accumulation)
                    # flush_interval=0.5: Flush every 0.5 seconds (prevents background worker 403s)
                    self.langfuse = Langfuse(
                        public_key=langfuse_public_key,
                        secret_key=langfuse_secret_key,
                        host=langfuse_host,
                        flush_at=1,  # Flush after 1 observation
                        flush_interval=0.5  # Flush every 0.5 seconds
                    )
                    info(f"Langfuse tracing enabled for model: {local_options.model}")
                except Exception as e:
                    info(f"Failed to initialize Langfuse: {e}")
                    self.langfuse = None
            else:
                info("Langfuse enabled but credentials not found. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")

        # Store PR context for Langfuse tracing
        self.pr_context = {
            "pr_number": None,
            "repository": os.getenv("GITHUB_REPOSITORY", "unknown"),
        }

        # Cache Langfuse configuration to avoid repeated environment variable parsing
        self.langfuse_config = {
            "truncate_limit": int(os.getenv("LANGFUSE_TRUNCATE_LIMIT", "500")),
            "log_content": os.getenv("LANGFUSE_LOG_CONTENT", "true").lower() == "true",
            "flush_strategy": os.getenv("LANGFUSE_FLUSH_STRATEGY", "batch"),
            "batch_size": int(os.getenv("LANGFUSE_BATCH_SIZE", "10"))
        }

        info(f"Initialized LocalBot with model: {self.model}")
        info(f"Ollama base URL: {self.base_url}")

    def set_pr_context(self, pr_number: int, repository: str = None):
        self.pr_context["pr_number"] = pr_number
        if repository:
            self.pr_context["repository"] = repository

    def flush_langfuse(self):
        """Manually flush any pending Langfuse data."""
        if self.langfuse:
            try:
                self.langfuse.flush()
                if self.options.debug:
                    info("Langfuse: Flushed all pending data")
            except Exception as e:
                info(f"Langfuse flush warning: {e}")

    def log_pr_review_metrics(
        self,
        files_reviewed: int,
        comments_generated: int,
        lines_of_code_reviewed: int
    ):
        """
        Log aggregate PR review metrics to Langfuse.
        This creates a separate event to track overall review statistics.
        """
        if not self.langfuse:
            return

        try:
            # Get PR context
            pr_number = self.pr_context.get("pr_number", "unknown")
            repo_name = self.pr_context.get("repository", "unknown")

            # Sanitize repository name
            sanitized_repo_name = repo_name.replace("Stellantis-ADX", "org").replace("Stellantis", "org")

            # Generate trace ID (same as used in chat() calls)
            trace_id = self.langfuse.create_trace_id(seed=f"pr-{sanitized_repo_name}-{pr_number}")
            trace_context = {"trace_id": trace_id}

            # Create event name for aggregate metrics
            event_name = f"{sanitized_repo_name.split('/')[-1]}-pr{pr_number}-review-metrics"

            # Log aggregate metrics as a generation event
            generation = self.langfuse.start_observation(
                as_type="generation",
                trace_context=trace_context,
                name=event_name,
                model=self.model,
                metadata={
                    "repository": sanitized_repo_name,
                    "pr_number": str(pr_number),
                    "files_reviewed": files_reviewed,
                    "comments_generated": comments_generated,
                    "lines_of_code_reviewed": lines_of_code_reviewed,
                    "review_type": "aggregate_metrics",
                    "ollama_base_url": self.base_url
                },
                level="DEFAULT"
            )

            generation.end()

            # Flush immediately to ensure metrics are logged
            self.langfuse.flush()

            if self.options.debug:
                info(f"Langfuse: Logged PR review metrics - Files: {files_reviewed}, Comments: {comments_generated}, LOC: {lines_of_code_reviewed}")

        except Exception as e:
            if self.options.debug:
                info(f"Langfuse: Failed to log PR review metrics: {e}")

    def _log_error_to_langfuse(
        self,
        error_msg: str,
        error_type: str,
        langfuse_trace_context: dict,
        langfuse_event_name: str,
        message: str,
        start: float,
        status_code: int = None
    ):
        """Helper method to log errors to Langfuse."""
        if not (langfuse_trace_context and self.langfuse):
            return

        try:
            truncate_limit = self.langfuse_config["truncate_limit"]

            metadata = {
                "error": error_msg,
                "error_type": error_type,
                "latency_ms": (time.time() - start) * 1000,
                "ollama_base_url": self.base_url,
                "repository": self.pr_context.get("repository", "unknown"),
                "pr_number": str(self.pr_context.get("pr_number", "unknown"))
            }

            if status_code:
                metadata["status_code"] = status_code

            generation = self.langfuse.start_observation(
                as_type="generation",
                trace_context=langfuse_trace_context,
                name=f"{langfuse_event_name or 'local-bot'}-error",
                input=message[:truncate_limit] if message else "",
                output=error_msg[:truncate_limit] if error_msg else "",
                model=self.model,
                model_parameters={
                    "temperature": float(self.options.model_temperature or 0.0),
                },
                metadata=metadata,
                level="ERROR",
                status_message=error_msg
            )
            generation.end()
            self.langfuse.flush()

        except Exception as log_error:
            if self.options.debug:
                info(f"Langfuse error logging failed: {log_error}")

    def __del__(self):
        """Cleanup: Flush Langfuse data and close HTTP client."""
        # Flush Langfuse
        if hasattr(self, 'langfuse') and self.langfuse:
            try:
                self.langfuse.flush()
            except:
                pass

        # Close HTTP client
        if hasattr(self, 'client') and self.client:
            try:
                self.client.close()
            except:
                pass
            
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

        # Prepare Langfuse tracking data
        langfuse_trace_context = None
        langfuse_event_name = None
        if self.langfuse:
            try:
                # Get PR context
                pr_number = self.pr_context.get("pr_number", "unknown")
                repo_name = self.pr_context.get("repository", "unknown")

                # Sanitize repository name to avoid corporate WAF/DLP blocking
                # This prevents 403 errors from corporate firewalls
                sanitized_repo_name = repo_name.replace("Stellantis-ADX", "org").replace("Stellantis", "org")

                # Generate unique trace ID using SANITIZED repository name
                trace_id = self.langfuse.create_trace_id(seed=f"pr-{sanitized_repo_name}-{pr_number}")

                # Create TraceContext (it's just a TypedDict)
                langfuse_trace_context = {"trace_id": trace_id}

                # Create unique generation name with SANITIZED PR context and timestamp
                repo_short = sanitized_repo_name.split('/')[-1] if '/' in sanitized_repo_name else sanitized_repo_name
                timestamp_ms = int(start * 1000)
                langfuse_event_name = f"{repo_short}-pr{pr_number}-{self.model}-{timestamp_ms}"

                if self.options.debug:
                    info(f"Langfuse trace_id: {trace_id}")
            except Exception as e:
                info(f"Failed to prepare Langfuse tracking: {e}")

        try:
            if self.options.debug:
                info(f"[LocalBot] POST {self.base_url}/api/generate model={self.model}")
                info(f"[LocalBot] Prompt chars: {len(prompt)}")

            # Make the request
            r = self.client.post("/api/generate", json=payload)

            # Capture time to first token (when response arrives)
            ttft_time = time.time()
            ttft_ms = (ttft_time - start) * 1000

            r.raise_for_status()
            data = r.json()

            # Ollama returns: {"response": "...", ...}
            text = (data.get("response") or "").strip()

            end = time.time()
            elapsed_ms = (end - start) * 1000
            info(f"Local/Ollama response time: {elapsed_ms:.2f} ms")

            if self.options.debug:
                info(f"[LocalBot] Response chars: {len(text)}")
                info(f"Time to first token (TTFT): {ttft_ms:.2f} ms")

            # Extract usage data if available (Ollama may not provide tokens)
            usage_data = {}
            if "prompt_eval_count" in data:
                usage_data["input"] = data.get("prompt_eval_count", 0)
            if "eval_count" in data:
                usage_data["output"] = data.get("eval_count", 0)
            if usage_data:
                usage_data["total"] = usage_data.get("input", 0) + usage_data.get("output", 0)
                if self.options.debug:
                    info(f"[LocalBot] Token usage - Input: {usage_data.get('input', 0)}, "
                         f"Output: {usage_data.get('output', 0)}, Total: {usage_data.get('total', 0)}")

            # Log to Langfuse (v3.14.5 API) - Use generation for cost tracking
            if langfuse_trace_context and self.langfuse:
                try:
                    # Sanitize repository name to avoid corporate WAF/DLP blocking
                    # Replace company identifiers with generic names
                    raw_repo = self.pr_context.get("repository", "unknown")
                    sanitized_repo = raw_repo.replace("Stellantis-ADX", "org").replace("Stellantis", "org")

                    # Create metadata with sanitized information
                    metadata = {
                        "repository": sanitized_repo,  # Sanitized to avoid WAF blocking
                        "pr_number": str(self.pr_context.get("pr_number", "unknown")),
                        "latency_ms": elapsed_ms,
                        "ttft_ms": ttft_ms,
                        "input_length": len(message),
                        "output_length": len(text),
                        "ollama_base_url": self.base_url
                    }

                    # Add review metrics if provided
                    if files_reviewed is not None:
                        metadata["files_reviewed"] = files_reviewed
                    if comments_generated is not None:
                        metadata["comments_generated"] = comments_generated
                    if lines_of_code_reviewed is not None:
                        metadata["lines_of_code_reviewed"] = lines_of_code_reviewed

                    # Prepare usage details for cost calculation (if available)
                    usage_details = None
                    if usage_data:
                        usage_details = {
                            "input": usage_data.get("input", 0),
                            "output": usage_data.get("output", 0),
                            "total": usage_data.get("total", 0)
                        }

                    # Get truncation limit and content logging settings
                    truncate_limit = self.langfuse_config["truncate_limit"]
                    log_content = self.langfuse_config["log_content"]

                    # Create generation (not event) for proper cost tracking
                    generation = self.langfuse.start_observation(
                        as_type="generation",
                        trace_context=langfuse_trace_context,
                        name=langfuse_event_name,
                        input=message[:truncate_limit] if (message and log_content) else None,
                        output=text[:truncate_limit] if (text and log_content) else None,
                        model=self.model,
                        model_parameters={
                            "temperature": float(self.options.model_temperature or 0.0),
                        },
                        usage_details=usage_details,
                        metadata=metadata,
                        level="DEFAULT"
                    )

                    # End the generation
                    generation.end()

                    # Flush strategy: immediate, batch, or manual
                    flush_strategy = self.langfuse_config["flush_strategy"]

                    if flush_strategy == "immediate":
                        # Flush immediately (may cause 403)
                        try:
                            self.langfuse.flush()
                            if self.options.debug:
                                info(f"Langfuse generation logged (immediate flush)")
                        except Exception as flush_error:
                            error_msg = str(flush_error)
                            if "403" in error_msg or "Forbidden" in error_msg:
                                info(f"Langfuse 403 error. Try LANGFUSE_FLUSH_STRATEGY=batch or LANGFUSE_LOG_CONTENT=false")
                            else:
                                info(f"Langfuse flush warning: {error_msg}")

                    elif flush_strategy == "batch":
                        # Let Langfuse batch internally (default, recommended)
                        if not hasattr(self, '_langfuse_call_count'):
                            self._langfuse_call_count = 0
                        self._langfuse_call_count += 1

                        # Flush every N calls (configurable)
                        batch_size = self.langfuse_config["batch_size"]
                        if self._langfuse_call_count % batch_size == 0:
                            try:
                                self.langfuse.flush()
                                # Small delay to prevent overwhelming server
                                time.sleep(0.1)
                                if self.options.debug:
                                    info(f"Langfuse batch flushed ({self._langfuse_call_count} calls)")
                            except Exception as flush_error:
                                error_msg = str(flush_error)
                                # Always log flush errors to diagnose issues
                                if "403" in error_msg or "Forbidden" in error_msg:
                                    info(f"⚠️  Langfuse 403 error on flush: {flush_error}")
                                else:
                                    info(f"Langfuse batch flush warning: {flush_error}")
                        elif self.options.debug:
                            info(f"Langfuse generation logged (batched, {self._langfuse_call_count % batch_size}/{batch_size})")

                    # For "manual" strategy, don't flush here

                except Exception as e:
                    # Don't fail the request if Langfuse logging fails
                    info(f"Langfuse logging failed (non-critical): {e}")

            return AiResponse(message=text)

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            info(f"[LocalBot] Failed to send message: {error_msg}")

            self._log_error_to_langfuse(
                error_msg=error_msg,
                error_type="HTTPStatusError",
                langfuse_trace_context=langfuse_trace_context,
                langfuse_event_name=langfuse_event_name,
                message=message,
                start=start,
                status_code=e.response.status_code
            )

            return AiResponse(message="")

        except Exception as e:
            error_msg = str(e)
            info(f"[LocalBot] Failed: {error_msg}")

            self._log_error_to_langfuse(
                error_msg=error_msg,
                error_type=type(e).__name__,
                langfuse_trace_context=langfuse_trace_context,
                langfuse_event_name=langfuse_event_name,
                message=message,
                start=start
            )

            return AiResponse(message="")
