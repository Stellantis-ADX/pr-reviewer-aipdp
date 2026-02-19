# Databricks Claude Integration Setup

This guide explains how to use Databricks-hosted Claude models (Opus and Sonnet) with the PR Reviewer AI.

## What Was Done

### 1. New Bot Implementation
Created [core/bots/bot_claude.py](core/bots/bot_claude.py) - A bot implementation that:
- Uses the Anthropic SDK to connect to Databricks-hosted Claude models
- Supports both Claude Opus 4.6 (for heavy/detailed reviews) and Claude Sonnet 4.5 (for light/summary tasks)
- Includes proper error handling and retry logic
- Logs detailed performance metrics

### 2. Updated Configuration System
Modified [core/schemas/options.py](core/schemas/options.py) to add:
- `databricks_base_url` - Your Databricks serving endpoint URL
- `databricks_token` - Your Databricks API token
- `light_model_name_claude` - Claude model for summaries (default: claude-sonnet-4-5)
- `heavy_model_name_claude` - Claude model for reviews (default: claude-opus-4-6)

### 3. Updated Token Limits
Modified [core/schemas/limits.py](core/schemas/limits.py) to support:
- Claude Opus 4.6: 200k context window, 16k response tokens
- Claude Sonnet 4.5: 200k context window, 8k response tokens
- Updated knowledge cutoff to 2025-01-01

### 4. Updated Main Entry Point
Modified [main.py](main.py) to:
- Import the new ClaudeBot
- Check for Databricks configuration
- Create Claude bots when Databricks credentials are provided
- Fallback to original HF/Azure bots if Databricks config is missing

### 5. Updated Dependencies
Modified [pyproject.toml](pyproject.toml) to add:
- `anthropic = "^0.40.0"` - Official Anthropic SDK

### 6. Updated Action Configuration
Modified [action.yml](action.yml) to add new inputs for Databricks Claude configuration.

## How to Use

### Step 1: Install Dependencies

```bash
cd pr-reviewer-ai
poetry install
# OR
poetry add anthropic
```

If using requirements.txt:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### Step 2: Configure Environment Variables

Copy the example environment file:
```bash
cp .env.databricks .env
```

Edit `.env` and fill in your values:

```bash
# Required: GitHub Configuration
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPOSITORY=your-org/your-repo

# Required: Databricks Claude Configuration
databricks_base_url=https://your-workspace.cloud.databricks.com/serving-endpoints
databricks_token=dapi1234567890abcdef
light_model_name_claude=claude-sonnet-4-5
heavy_model_name_claude=claude-opus-4-6
```

### Step 3: Get Databricks Credentials

1. **Base URL**:
   - Go to your Databricks workspace
   - Navigate to Serving → Endpoints
   - Your base URL format: `https://<workspace-id>.cloud.databricks.com/serving-endpoints`

2. **API Token**:
   - In Databricks, go to User Settings
   - Click "Access Tokens"
   - Generate new token
   - Copy the token (starts with `dapi`)

3. **Model Names**:
   - Use the exact model names from your Databricks serving endpoints
   - Typical names: `claude-opus-4-6`, `claude-sonnet-4-5`
   - Or custom names like: `databricks-claude-opus-4-6`

### Step 4: Test Locally

```bash
# Set environment variables
export $(cat .env | grep -v '^#' | xargs)

# Run the bot
python main.py
```

### Step 5: Configure GitHub Action

Update your `.github/workflows/pr-reviewer-ai.yml`:

```yaml
name: Code Review

permissions:
  contents: read
  pull-requests: write

on:
  pull_request:
  pull_request_review_comment:
    types: [created]

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: "Action Setup Python"
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: "AI PR Reviewer"
        uses: your-org/pr-reviewer-ai@main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          # Databricks Claude Configuration
          databricks_base_url: ${{ secrets.DATABRICKS_BASE_URL }}
          databricks_token: ${{ secrets.DATABRICKS_TOKEN }}
          light_model_name_claude: 'claude-sonnet-4-5'
          heavy_model_name_claude: 'claude-opus-4-6'

          # Review Settings
          debug: 'false'
          less_spammy: 'true'
          review_simple_changes: 'false'
          review_comment_lgtm: 'false'
          allow_empty_review: 'false'
```

### Step 6: Add GitHub Secrets

In your repository settings (Settings → Secrets and variables → Actions), add:

- `DATABRICKS_BASE_URL` - Your Databricks serving endpoint URL
- `DATABRICKS_TOKEN` - Your Databricks API token

## Architecture Flow

```
GitHub PR Event
      ↓
   main.py
      ↓
Check for databricks_token & databricks_base_url
      ↓
   ┌──────────────────┬──────────────────┐
   │ If configured:   │ If not:          │
   │ Use ClaudeBot    │ Use HFBot/Azure  │
   └──────────────────┴──────────────────┘
      ↓                       ↓
Create 2 Claude bots:    Create 2 HF/Azure bots:
- Light (Sonnet)         - Light (Mistral Small)
- Heavy (Opus)           - Heavy (Mistral Large)
      ↓
Process PR Review
```

## Model Selection Guide

### Light Model (Sonnet) - For Summaries
- **Use**: File summaries, quick triage
- **Model**: `claude-sonnet-4-5`
- **Context**: 200k tokens
- **Response**: Up to 8k tokens
- **Speed**: Fast
- **Cost**: Lower

### Heavy Model (Opus) - For Reviews
- **Use**: Detailed code review, suggestions
- **Model**: `claude-opus-4-6`
- **Context**: 200k tokens
- **Response**: Up to 16k tokens
- **Speed**: Slower but thorough
- **Cost**: Higher

## Troubleshooting

### Error: "Unable to initialize the Claude API"
- Check that `databricks_base_url` and `databricks_token` are set
- Verify the token is valid and not expired
- Ensure the URL format is correct

### Error: "Model not found"
- Check that the model names match your Databricks serving endpoints
- Go to Databricks Serving → Endpoints to verify model names
- Try using the exact endpoint name from Databricks

### Error: Connection timeout
- Increase `timeout_ms` in configuration
- Check Databricks serving endpoint status
- Verify network connectivity to Databricks

### Debug Mode
Enable debug mode to see detailed logs:
```yaml
with:
  debug: 'true'
```

This will show:
- Request/response details
- Token usage
- Performance metrics
- Error stack traces

## Benefits of Using Claude

1. **Large Context Window**: 200k tokens allows reviewing large files
2. **Better Code Understanding**: Strong reasoning for complex code patterns
3. **Detailed Reviews**: More thorough analysis with actionable suggestions
4. **Modern Knowledge**: Updated cutoff date (2025-01)
5. **Privacy**: Runs on your Databricks infrastructure

## Cost Optimization

To reduce costs:
1. Set `less_spammy: 'true'` - Removes redundant comments
2. Set `review_simple_changes: 'false'` - Skips trivial changes
3. Set `max_files: 50` - Limit number of files reviewed
4. Use Sonnet for both if reviews are simpler:
   ```yaml
   light_model_name_claude: 'claude-sonnet-4-5'
   heavy_model_name_claude: 'claude-sonnet-4-5'
   ```

## Next Steps

1. ✅ Install dependencies with `poetry install`
2. ✅ Configure `.env` file with your Databricks credentials
3. ✅ Test locally with a sample PR
4. ✅ Add secrets to GitHub repository
5. ✅ Update GitHub Action workflow
6. ✅ Create a test PR to verify the setup

## Support

For issues or questions:
- Check logs with `debug: 'true'`
- Verify Databricks endpoint status
- Review [bot_claude.py](core/bots/bot_claude.py) implementation
- Check Anthropic SDK documentation: https://docs.anthropic.com
