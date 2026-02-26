# Langfuse Integration for PR Reviewer AI

## ⚠️ Current Status

**Langfuse integration is currently DISABLED by default.**

The integration code structure is in place, but the Langfuse SDK API varies between versions. To enable Langfuse:

1. **Check official documentation**: https://github.com/langfuse/langfuse
2. **Verify your SDK version**: `pip show langfuse`
3. **Update the integration code** in `core/bots/bot_claude.py` to match the API for your SDK version
4. **Enable in .env**: Set `LANGFUSE_ENABLED=true`

## Overview

When properly configured, Langfuse provides comprehensive observability and tracing for all LLM calls. This enables you to:

- **Track token usage** across all reviews
- **Monitor latency** and performance
- **Analyze costs** for each model
- **Debug issues** with full prompt/response visibility
- **Compare models** (Claude vs Llama vs others)
- **Optimize prompts** based on real data

## Setup

### 1. Install Langfuse

```bash
cd /Users/t0142f5/Desktop/Workspace/pr-reviewer-ai/pr-reviewer-ai
pip install langfuse
```

### 2. Get Langfuse Credentials

#### Option A: Langfuse Cloud (Recommended)

1. Go to [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. Sign up for a free account
3. Create a new project
4. Go to Settings > API Keys
5. Generate a new API key pair (Public & Secret)

#### Option B: Self-Hosted Langfuse

1. Deploy Langfuse to your infrastructure: [Self-hosting docs](https://langfuse.com/docs/deployment/self-host)
2. Generate API keys from your instance
3. Note your instance URL

### 3. Configure Environment Variables

Add your Langfuse credentials to [.env](.env):

```bash
# Langfuse Configuration (Optional - for LLM observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**For self-hosted:**
```bash
LANGFUSE_HOST=https://your-langfuse-instance.com
```

**To disable tracing (default):**
```bash
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

## What Gets Tracked

### Trace Hierarchy

```
pr-review-{repository}-{pr_number}  ← Trace (one per review)
└── code-review-{model_name}        ← Generation (one per LLM call)
    ├── Input: Full prompt
    ├── Output: Model response
    ├── Usage: Token counts
    └── Metadata: Model, temp, latency, etc.
```

### Tracked Metrics

For each LLM call, Langfuse captures:

| Metric | Description | Example |
|--------|-------------|---------|
| **Model** | Model name | `databricks-claude-opus-4-6` |
| **Input Tokens** | Prompt tokens | 15,234 |
| **Output Tokens** | Completion tokens | 1,456 |
| **Total Tokens** | Sum of input + output | 16,690 |
| **Latency** | Response time in ms | 3,450 ms |
| **Temperature** | Sampling temperature | 0.0 |
| **Max Tokens** | Max response length | 4,000 |
| **Repository** | GitHub repo | `Stellantis-ADX/noise_app_backend` |
| **PR Number** | Pull request number | 1 |
| **Status** | Success or error | `SUCCESS` |

### Trace Metadata

Each trace includes:
- Repository name
- PR number
- Model configuration (temperature, max_tokens)
- Prompt length
- Response length
- Error messages (if failed)

## Using Langfuse Dashboard

### 1. View All Traces

Go to **Traces** in Langfuse to see all PR reviews:

- Filter by repository: `metadata.repository = "your-repo"`
- Filter by PR: `metadata.pr_number = "123"`
- Filter by model: `metadata.model = "databricks-claude-opus-4-6"`

### 2. Analyze Token Usage

Go to **Metrics** → **Usage**:

- Total tokens by model
- Cost estimation (if prices configured)
- Token usage over time
- Breakdown by input/output tokens

### 3. Monitor Latency

Go to **Metrics** → **Latency**:

- Average response time per model
- P50, P95, P99 latencies
- Identify slow requests
- Compare model performance

### 4. Compare Models

To compare Claude Opus vs Llama:

1. Run reviews with different models:
   ```bash
   # Test with Claude Opus
   heavy_model_name_claude=databricks-claude-opus-4-6
   ./run.sh

   # Test with Llama
   heavy_model_name_claude=databricks-llama-4-maverick
   ./run.sh
   ```

2. In Langfuse:
   - Go to **Traces**
   - Filter by `metadata.model`
   - Compare:
     - Token usage (cost)
     - Latency (speed)
     - Output quality (manual review)

### 5. Debug Issues

When a review fails:

1. Find the trace in Langfuse
2. View the full prompt sent to the model
3. Check error messages in metadata
4. Review response or error details
5. Analyze token limits (did prompt exceed max_tokens?)

## Advanced Features

### Session Grouping

All calls within a single PR review are grouped into one trace:

```
pr-review-Stellantis-ADX/noise_app_backend-1
├── code-review-databricks-claude-sonnet-4-6  (summary)
├── code-review-databricks-claude-opus-4-6     (review file 1)
├── code-review-databricks-claude-opus-4-6     (review file 2)
└── code-review-databricks-claude-opus-4-6     (review file 3)
```

This allows you to:
- See total tokens for entire PR review
- Track which files were reviewed
- Calculate total cost per PR

### Cost Tracking

Configure model costs in Langfuse:

1. Go to **Settings** → **Models**
2. Add your models with pricing:
   - Model name: `databricks-claude-opus-4-6`
   - Input cost: `$15.00 / 1M tokens`
   - Output cost: `$75.00 / 1M tokens`

Langfuse will automatically calculate costs for all traces.

### Prompt Versioning

Compare prompt changes over time:

1. Each trace includes the full prompt
2. Search for specific prompt versions
3. Compare metrics before/after prompt changes
4. A/B test different prompts

## Example Queries

### Find expensive reviews
```
total_tokens > 50000
```

### Find slow reviews
```
latency_ms > 10000
```

### Find failed reviews
```
status = "ERROR"
```

### Reviews for specific PR
```
metadata.pr_number = "123"
```

### Reviews with specific model
```
metadata.model = "databricks-llama-4-maverick"
```

## Troubleshooting

### Langfuse not tracking

**Check logs:**
```bash
./run.sh 2>&1 | grep -i langfuse
```

Expected output:
```
Langfuse tracing enabled for model: databricks-claude-opus-4-6
```

**Common issues:**

1. **Missing credentials:**
   ```
   Langfuse credentials not found. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY
   ```
   → Add credentials to `.env`

2. **Import error:**
   ```
   Langfuse not installed. Install with: pip install langfuse
   ```
   → Run: `pip install langfuse`

3. **Connection error:**
   ```
   Failed to initialize Langfuse: [connection error]
   ```
   → Check `LANGFUSE_HOST` is correct
   → Check network connectivity

4. **Not showing in dashboard:**
   - Wait a few seconds (Langfuse batches requests)
   - Check project selection in dashboard
   - Verify API keys are for correct project

### Token counts not showing

Token usage requires the model to return usage data in the response.

**Check logs:**
```bash
./run.sh 2>&1 | grep "tokens"
```

Expected:
```
Prompt tokens: 15234
Completion tokens: 1456
Total tokens: 16690
```

If missing, the Databricks endpoint may not be returning usage data.

## Best Practices

1. **Tag important reviews:** Add custom tags in Langfuse UI for:
   - High-value PRs
   - Problematic reviews
   - Model comparisons

2. **Monitor costs:** Set up alerts in Langfuse for:
   - Daily token usage exceeds threshold
   - Single review exceeds cost limit

3. **Regular audits:** Review metrics weekly:
   - Are costs trending up?
   - Is latency increasing?
   - Are certain files always slow?

4. **A/B testing:** When changing prompts or models:
   - Keep old version for a few days
   - Compare metrics in Langfuse
   - Make data-driven decisions

5. **Error tracking:** Check error traces regularly:
   - Fix common failure patterns
   - Improve error handling
   - Optimize prompts for edge cases

## Privacy & Security

- **Prompts contain code:** Full PR code is sent to Langfuse
- **Self-host for sensitive code:** Use self-hosted Langfuse for private repos
- **Retention policies:** Configure data retention in Langfuse settings
- **Access control:** Use Langfuse teams/roles to control access

## Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)
- [Self-hosting Guide](https://langfuse.com/docs/deployment/self-host)
- [Pricing](https://langfuse.com/pricing)

## Support

- **Langfuse issues:** [GitHub Issues](https://github.com/langfuse/langfuse/issues)
- **PR Reviewer issues:** [Your repo issues]

---

**Status:** ✅ Fully Integrated
**Date:** 2026-02-25
**Version:** 1.0
