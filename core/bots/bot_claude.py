import json
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

        # Initialize Langfuse for observability (v3.14.5 API)
        self.langfuse = None
        langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

        if LANGFUSE_AVAILABLE and langfuse_enabled:
            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

            if langfuse_public_key and langfuse_secret_key:
                try:
                    self.langfuse = Langfuse(
                        public_key=langfuse_public_key,
                        secret_key=langfuse_secret_key,
                        host=langfuse_host
                    )
                    info(f"Langfuse tracing enabled for model: {claude_options.model}")
                except Exception as e:
                    info(f"Failed to initialize Langfuse: {e}")
                    self.langfuse = None
            else:
                info("Langfuse credentials found but LANGFUSE_ENABLED not set to 'true'")

        # Store PR context for Langfuse tracing
        self.pr_context = {
            "pr_number": None,
            "repository": os.getenv("GITHUB_REPOSITORY", "unknown")
        }

        info(f"Initialized Claude bot with model: {claude_options.model}")
        info(f"Using Databricks endpoint: {base_url}")

    def set_pr_context(self, pr_number: int, repository: str = None):
        """Set PR context for Langfuse tracing."""
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
        Called at the end of the review process with aggregated metrics.
        """
        if not self.langfuse:
            return

        try:
            # Get PR context
            pr_number = self.pr_context.get("pr_number", "unknown")
            repo_name = self.pr_context.get("repository", "unknown")

            # Generate trace ID (same as used in chat() calls)
            trace_id = self.langfuse.create_trace_id(seed=f"pr-{repo_name}-{pr_number}")
            trace_context = {"trace_id": trace_id}

            # Create event name for aggregate metrics
            repo_short = repo_name.split('/')[-1] if '/' in repo_name else repo_name
            event_name = f"{repo_short}-pr{pr_number}-aggregate-metrics"

            # Log aggregate metrics as a generation event
            generation = self.langfuse.start_observation(
                as_type="generation",
                trace_context=trace_context,
                name=event_name,
                model=self.api["model"],
                metadata={
                    "repository": repo_name,  # Use actual repo name, not sanitized
                    "pr_number": str(pr_number),
                    "files_reviewed": files_reviewed,
                    "comments_generated": comments_generated,
                    "lines_of_code_reviewed": lines_of_code_reviewed,
                    "review_type": "aggregate_metrics"
                },
                level="DEFAULT"
            )

            generation.end()

            # Flush immediately to ensure metrics are logged
            self.langfuse.flush()

            if self.options.debug:
                info(f"Langfuse: Logged aggregate metrics - Files: {files_reviewed}, "
                     f"Comments: {comments_generated}, LOC: {lines_of_code_reviewed}")

        except Exception as e:
            if self.options.debug:
                info(f"Langfuse: Failed to log aggregate metrics: {e}")

    def __del__(self):
        """Cleanup: Flush Langfuse data on bot destruction."""
        if hasattr(self, 'langfuse') and self.langfuse:
            try:
                self.langfuse.flush()
            except:
                pass  # Silent cleanup

    def chat(
        self,
        message: str,
        files_reviewed: int = None,
        comments_generated: int = None,
        lines_of_code_reviewed: int = None
    ) -> AiResponse:
        """
        Send a message to Claude via Databricks serving endpoint.

        Args:
            message: The prompt to send to Claude
            files_reviewed: Number of files reviewed (for Langfuse tracking)
            comments_generated: Number of comments generated (for Langfuse tracking)
            lines_of_code_reviewed: Total lines of code reviewed (for Langfuse tracking)
        """
        start = time.time()

        if not message:
            return AiResponse()

        response = None
        response_text = ""
        usage_data = {}

        # Prepare Langfuse tracking data
        langfuse_trace_context = None
        langfuse_event_name = None
        if self.langfuse:
            try:
                # Get PR context
                pr_number = self.pr_context.get("pr_number", "unknown")
                repo_name = self.pr_context.get("repository", "unknown")

                # Generate unique trace ID using Langfuse method
                trace_id = self.langfuse.create_trace_id(seed=f"pr-{repo_name}-{pr_number}")

                # Create TraceContext (it's just a TypedDict)
                langfuse_trace_context = {"trace_id": trace_id}

                # Create unique generation name with PR context and timestamp
                repo_short = repo_name.split('/')[-1] if '/' in repo_name else repo_name
                timestamp_ms = int(start * 1000)
                langfuse_event_name = f"{repo_short}-pr{pr_number}-{self.api['model']}-{timestamp_ms}"

                if self.options.debug:
                    info(f"Langfuse trace_id: {trace_id}")
            except Exception as e:
                info(f"Failed to prepare Langfuse tracking: {e}")

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

            # Capture time to first token (when response headers arrive)
            ttft_time = time.time()
            ttft_ms = (ttft_time - start) * 1000

            # Check for errors
            http_response.raise_for_status()

            # Parse response
            response_json = http_response.json()

            if self.options.debug:
                info(f"Response status: {http_response.status_code}")

            # Extract the text from the response
            # Databricks returns OpenAI-compatible format: choices[0].message.content
            if "choices" in response_json and len(response_json["choices"]) > 0:
                message_data = response_json["choices"][0].get("message", {})
                response_text = message_data.get("content", "")

                # Extract usage data for Langfuse
                if "usage" in response_json:
                    usage_data = {
                        "input": response_json['usage'].get('prompt_tokens', 0),
                        "output": response_json['usage'].get('completion_tokens', 0),
                        "total": response_json['usage'].get('total_tokens', 0)
                    }

                    if self.options.debug:
                        info(f"Claude response length: {len(response_text)} characters")
                        info(f"Prompt tokens: {usage_data['input']}")
                        info(f"Completion tokens: {usage_data['output']}")
                        info(f"Total tokens: {usage_data['total']}")
            else:
                info("Claude API returned empty content")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            info(f"Failed to send message to Claude API: {error_msg}")

            # Log error to Langfuse as generation with ERROR level
            if langfuse_trace_context and self.langfuse:
                try:
                    truncate_limit = int(os.getenv("LANGFUSE_TRUNCATE_LIMIT", "500"))
                    generation = self.langfuse.start_observation(
                        as_type="generation",
                        trace_context=langfuse_trace_context,
                        name=f"{langfuse_event_name}-error",
                        input=message[:truncate_limit] if message else "",
                        output=error_msg[:truncate_limit] if error_msg else "",
                        model=self.api['model'],
                        model_parameters={
                            "temperature": self.api["temperature"],
                            "max_tokens": self.api["max_response_tokens"]
                        },
                        metadata={
                            "error": error_msg,
                            "error_type": "HTTPStatusError",
                            "status_code": e.response.status_code,
                            "latency_ms": (time.time() - start) * 1000,
                            "repository": self.pr_context.get("repository", "unknown"),
                            "pr_number": str(self.pr_context.get("pr_number", "unknown"))
                        },
                        level="ERROR",
                        status_message=error_msg
                    )
                    generation.end()
                    self.langfuse.flush()
                except Exception as log_error:
                    if self.options.debug:
                        info(f"Langfuse error logging failed: {log_error}")

            return AiResponse(message="")

        except Exception as e:
            error_msg = str(e)
            info(f"Failed to send message to Claude API: {error_msg}")

            # Log error to Langfuse as generation with ERROR level
            if langfuse_trace_context and self.langfuse:
                try:
                    truncate_limit = int(os.getenv("LANGFUSE_TRUNCATE_LIMIT", "500"))
                    generation = self.langfuse.start_observation(
                        as_type="generation",
                        trace_context=langfuse_trace_context,
                        name=f"{langfuse_event_name}-error",
                        input=message[:truncate_limit] if message else "",
                        output=error_msg[:truncate_limit] if error_msg else "",
                        model=self.api['model'],
                        model_parameters={
                            "temperature": self.api["temperature"],
                            "max_tokens": self.api["max_response_tokens"]
                        },
                        metadata={
                            "error": error_msg,
                            "error_type": type(e).__name__,
                            "latency_ms": (time.time() - start) * 1000,
                            "repository": self.pr_context.get("repository", "unknown"),
                            "pr_number": str(self.pr_context.get("pr_number", "unknown"))
                        },
                        level="ERROR",
                        status_message=error_msg
                    )
                    generation.end()
                    self.langfuse.flush()
                except Exception as log_error:
                    if self.options.debug:
                        info(f"Langfuse error logging failed: {log_error}")

            return AiResponse(message="")

        end = time.time()
        elapsed_ms = (end - start) * 1000

        info(f"Claude API response time: {elapsed_ms:.2f} ms")
        if self.options.debug:
            info(f"Time to first token (TTFT): {ttft_ms:.2f} ms")

        # Clean up response text (remove common prefixes)
        if response_text.startswith("with "):
            response_text = response_text[5:]

        if self.options.debug:
            info(f"[DEBUG] Full Claude response:")
            info(f"--- RESPONSE START ---")
            info(response_text[:3000] + "..." if len(response_text) > 3000 else response_text)
            info(f"--- RESPONSE END (showing first 3000 chars) ---")

        # Log to Langfuse (v3.14.5 API) - Use generation for cost tracking
        if langfuse_trace_context and self.langfuse:
            try:
                # Create metadata with all relevant information
                metadata = {
                    "repository": self.pr_context.get("repository", "unknown"),
                    "pr_number": str(self.pr_context.get("pr_number", "unknown")),
                    "latency_ms": elapsed_ms,
                    "ttft_ms": ttft_ms,  # Time to first token
                    "input_length": len(message),
                    "output_length": len(response_text)
                }

                # Add review metrics if provided
                if files_reviewed is not None:
                    metadata["files_reviewed"] = files_reviewed
                if comments_generated is not None:
                    metadata["comments_generated"] = comments_generated
                if lines_of_code_reviewed is not None:
                    metadata["lines_of_code_reviewed"] = lines_of_code_reviewed

                # Prepare usage details for cost calculation
                usage_details = None
                if usage_data:
                    usage_details = {
                        "input": usage_data.get("input", 0),
                        "output": usage_data.get("output", 0),
                        "total": usage_data.get("total", 0)
                    }

                # Get truncation limit from environment (default 500 for large code reviews)
                truncate_limit = int(os.getenv("LANGFUSE_TRUNCATE_LIMIT", "500"))

                # Option to disable content logging entirely (only log metadata)
                log_content = os.getenv("LANGFUSE_LOG_CONTENT", "true").lower() == "true"

                # Create generation (not event) for proper cost tracking
                generation = self.langfuse.start_observation(
                    as_type="generation",
                    trace_context=langfuse_trace_context,
                    name=langfuse_event_name,
                    input=message[:truncate_limit] if (message and log_content) else None,
                    output=response_text[:truncate_limit] if (response_text and log_content) else None,
                    model=self.api['model'],
                    model_parameters={
                        "temperature": self.api["temperature"],
                        "max_tokens": self.api["max_response_tokens"]
                    },
                    usage_details=usage_details,
                    metadata=metadata,
                    level="DEFAULT"
                )

                # End the generation
                generation.end()

                # Flush strategy: immediate, batch, or manual
                flush_strategy = os.getenv("LANGFUSE_FLUSH_STRATEGY", "batch")

                if flush_strategy == "immediate":
                    # Flush immediately (old behavior, may cause 403)
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
                    # Only flush periodically to avoid 403
                    if not hasattr(self, '_langfuse_call_count'):
                        self._langfuse_call_count = 0
                    self._langfuse_call_count += 1

                    # Flush every N calls (configurable)
                    batch_size = int(os.getenv("LANGFUSE_BATCH_SIZE", "10"))
                    if self._langfuse_call_count % batch_size == 0:
                        try:
                            self.langfuse.flush()
                            if self.options.debug:
                                info(f"Langfuse batch flushed ({self._langfuse_call_count} calls)")
                        except Exception as flush_error:
                            info(f"Langfuse batch flush warning: {flush_error}")
                    elif self.options.debug:
                        info(f"Langfuse generation logged (batched, {self._langfuse_call_count % batch_size}/{batch_size})")

                # For "manual" strategy, don't flush here (flush at end of review)

            except Exception as e:
                # Don't fail the request if Langfuse logging fails
                info(f"Langfuse logging failed (non-critical): {e}")

        return AiResponse(message=response_text)
