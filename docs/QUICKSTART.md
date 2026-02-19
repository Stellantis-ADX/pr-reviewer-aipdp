# Quick Start Guide - Databricks Claude PR Reviewer

## ✅ Setup Complete!

Your Databricks Claude integration is now working! Here's what you need to know:

## Current Configuration

- **Databricks URL**: `https://dbc-deebf286-07d0.cloud.databricks.com/serving-endpoints`
- **Light Model**: `databricks-claude-sonnet-4-6` ✅ Working!
- **Heavy Model**: `databricks-claude-opus-4-6`
- **Environment**: `.env` file configured

## Files You Need to Know

### Configuration
- **`.env`** - Your environment configuration (already set up)
- **`pyproject.toml`** - Dependencies (anthropic SDK added)

### Bot Implementation
- **`core/bots/bot_claude.py`** - Databricks Claude bot (uses httpx with Bearer auth)
- **`main.py`** - Main entry point (updated to use Claude bots)

### Testing & Running
- **`test_claude_bot.py`** - Test script to verify connection
- **`run.sh`** - Convenient run script for local testing

### Documentation
- **`DATABRICKS_CLAUDE_SETUP.md`** - Detailed setup guide
- **`IMPLEMENTATION_SUMMARY.md`** - Complete change summary
- **`.github-workflow-example.yml`** - GitHub Actions template

## Quick Commands

### Test the Bot Connection
```bash
source venv/bin/activate
python test_claude_bot.py
```

### Run Locally (requires GitHub event)
```bash
./run.sh
```

### Install/Update Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
# Or just: pip install anthropic httpx
```

## How It Works

1. **Authentication**: Uses Bearer token (`Authorization: Bearer <token>`)
2. **Request Format**: Sends Anthropic Messages API format
3. **Response Format**: Receives OpenAI-compatible format
4. **Endpoint URL**: `{base_url}/{model_name}/invocations`

## Model Details

### databricks-claude-sonnet-4-6 (Light Model)
- **Context Window**: 200,000 tokens
- **Response Limit**: 8,000 tokens
- **Use Case**: Quick summaries, file triage
- **Speed**: Fast (~3-4 seconds)

### databricks-claude-opus-4-6 (Heavy Model)
- **Context Window**: 200,000 tokens
- **Response Limit**: 16,000 tokens
- **Use Case**: Detailed code review, complex analysis
- **Speed**: Slower but more thorough

## Using in GitHub Actions

1. Add secrets to your repo:
   - `DATABRICKS_BASE_URL`
   - `DATABRICKS_TOKEN`

2. Use the example workflow:
```yaml
- name: "AI PR Reviewer"
  uses: your-org/pr-reviewer-ai@main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    databricks_base_url: ${{ secrets.DATABRICKS_BASE_URL }}
    databricks_token: ${{ secrets.DATABRICKS_TOKEN }}
    light_model_name_claude: 'databricks-claude-sonnet-4-6'
    heavy_model_name_claude: 'databricks-claude-opus-4-6'
    debug: 'false'
    less_spammy: 'true'
```

## Troubleshooting

### If you get 401 errors:
- Check your Databricks token is valid
- Verify the token hasn't expired
- Ensure you're using the correct workspace URL

### If you get 404 errors:
- Verify the model endpoint name matches your Databricks serving endpoint exactly
- Check the endpoint is deployed and active in Databricks

### If responses are empty:
- Enable debug mode: `debug=true` in `.env`
- Check the logs for response format issues

### Enable Debug Mode:
Edit `.env` and set:
```bash
debug=true
```

Then run the test:
```bash
python test_claude_bot.py
```

## Next Steps

1. ✅ Test with a real PR:
   - Set `GITHUB_EVENT_PATH` to point to a real PR event JSON
   - Run `./run.sh`

2. ✅ Deploy to GitHub Actions:
   - Copy `.github-workflow-example.yml` to `.github/workflows/`
   - Add secrets to your repository
   - Create a test PR

3. ✅ Customize behavior:
   - Edit prompts in `action.yml`
   - Adjust settings in `.env`
   - Modify `core/templates/prompts.py`

## Support

- **Test Connection**: `python test_claude_bot.py`
- **Check Bot Code**: `core/bots/bot_claude.py`
- **View Full Docs**: `DATABRICKS_CLAUDE_SETUP.md`

---

**Status**: ✅ Fully Functional
**Tested**: 2026-02-19
**Response Time**: ~3-4 seconds per request
