class TokenLimits:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.knowledge_cut_off = "2025-01-01"
        if model == "gpt-4-32k":
            self.max_tokens = 32600
            self.response_tokens = 4000
        elif model == "gpt-3.5-turbo-16k":
            self.max_tokens = 16300
            self.response_tokens = 3000
        elif model == "gpt-4":
            self.max_tokens = 8000
            self.response_tokens = 2000
        elif model == "small":
            self.max_tokens = 3100
            self.response_tokens = 1000
        elif model == "big":
            # TODO change once big model is deployed
            self.max_tokens = 32600
            self.response_tokens = 4000
        elif model == "mistral-small-azure":
            self.max_tokens = 4000
            self.response_tokens = 1000
        elif model == "mistral-large-azure":
            self.max_tokens = 32600
            self.response_tokens = 4000
        # Claude models (Databricks)
        elif model in ("claude-opus-4-6", "databricks-claude-opus-4-6"):
            self.max_tokens = 200000
            self.response_tokens = 16000
            self.knowledge_cut_off = "2025-01-01"
        elif model in ("claude-sonnet-4-5", "databricks-claude-sonnet-4-5"):
            self.max_tokens = 200000
            self.response_tokens = 8000
            self.knowledge_cut_off = "2025-01-01"
        elif model.startswith("claude-"):
            # Generic Claude model fallback
            self.max_tokens = 200000
            self.response_tokens = 8000
            self.knowledge_cut_off = "2025-01-01"
        else:
            self.max_tokens = 4000
            self.response_tokens = 1000
        # provide some margin for the request tokens
        self.request_tokens = self.max_tokens - self.response_tokens - 100

    def __str__(self):
        return (
            f"max_tokens={self.max_tokens}, "
            f"request_tokens={self.request_tokens}, "
            f"response_tokens={self.response_tokens}"
        )
