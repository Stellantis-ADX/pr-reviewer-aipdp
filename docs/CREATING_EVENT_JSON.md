# Creating GitHub Event JSON for Local Testing

When testing the PR Reviewer AI locally, you need to provide a GitHub event JSON file that simulates a pull request event. Here are three ways to create one:

## Method 1: Use the Generator Script (Recommended)

Use the provided script to fetch real PR data:

```bash
# Activate virtual environment
source venv/bin/activate

# Generate from a real PR
export GITHUB_TOKEN=ghp_your_token_here
python generate_event.py owner/repo-name 123

# Example
python generate_event.py octocat/Hello-World 1
```

This will:
- ✅ Fetch real PR data from GitHub
- ✅ Create `test/pr_123_event.json`
- ✅ Include actual PR title, description, and stats

**If no token is set**, it creates a template you can edit manually.

## Method 2: Use the Template

A simple template has been created at `test/my_pull_request.json`. Edit it with your details:

```json
{
  "action": "opened",
  "number": 1,
  "pull_request": {
    "number": 1,
    "title": "Your PR title",
    "body": "Your PR description",
    "base": {
      "ref": "main",
      "repo": {
        "full_name": "your-username/your-repo"
      }
    },
    "head": {
      "ref": "feature-branch"
    }
  },
  "repository": {
    "full_name": "your-username/your-repo"
  }
}
```

**Key fields to update:**
- `number` - PR number
- `title` - PR title
- `body` - PR description
- `repository.full_name` - Your repo (format: `owner/repo`)
- `base.ref` - Target branch (usually `main` or `master`)
- `head.ref` - Your feature branch name

## Method 3: Download from GitHub Actions

If you've already run the action on GitHub, you can download the event JSON:

1. Go to your GitHub Actions run
2. Click on the failed/completed run
3. Look for artifacts or download the event JSON
4. Or use GitHub API:

```bash
# Get the event JSON from a workflow run
gh api /repos/OWNER/REPO/actions/runs/RUN_ID/artifacts
```

## Using Your Event JSON

### Option A: Update .env file

Edit your `.env` file:

```bash
GITHUB_EVENT_PATH=test/my_pull_request.json
# or
GITHUB_EVENT_PATH=test/pr_123_event.json
```

### Option B: Export Environment Variable

```bash
export GITHUB_EVENT_PATH=test/my_pull_request.json
```

### Option C: Use in run.sh

The `run.sh` script automatically loads from `.env`, so just set it there.

## Required Fields

The PR Reviewer AI requires these fields in the event JSON:

### Essential Fields:
- ✅ `number` - PR number
- ✅ `pull_request.number` - PR number (same as above)
- ✅ `pull_request.base.ref` - Target branch
- ✅ `pull_request.head.ref` - Source branch
- ✅ `pull_request.base.sha` - Base commit SHA
- ✅ `pull_request.head.sha` - Head commit SHA
- ✅ `repository.full_name` - Repository name (owner/repo)
- ✅ `repository.owner.login` - Repository owner

### Optional but Helpful:
- `pull_request.title` - PR title
- `pull_request.body` - PR description
- `pull_request.additions` - Lines added
- `pull_request.deletions` - Lines deleted
- `pull_request.changed_files` - Number of files changed

## Example Workflows

### Test with a Real PR

```bash
# 1. Generate event from real PR
export GITHUB_TOKEN=ghp_your_token
python generate_event.py your-username/your-repo 42

# 2. Update .env to use it
echo "GITHUB_EVENT_PATH=test/pr_42_event.json" >> .env

# 3. Run the reviewer
./run.sh
```

### Test with a Template

```bash
# 1. Copy and edit template
cp test/my_pull_request.json test/test_pr.json
# Edit test/test_pr.json with your details

# 2. Update .env
echo "GITHUB_EVENT_PATH=test/test_pr.json" >> .env

# 3. Run the reviewer
./run.sh
```

## Troubleshooting

### "GITHUB_EVENT_PATH does not exist"
- Check the file path is correct
- Use relative path from project root: `test/my_pull_request.json`
- Or use absolute path: `/full/path/to/event.json`

### "Repository not found"
- Verify `GITHUB_TOKEN` has access to the repository
- Check `repository.full_name` format is `owner/repo`
- Ensure repository actually exists

### "Pull request not found"
- Verify the PR number exists in the repository
- Check you have permission to access the PR
- Try with a different, newer PR

### "Invalid JSON"
- Validate your JSON: `python -m json.tool test/my_pull_request.json`
- Check for missing commas, quotes, or brackets
- Use a JSON validator online

## Quick Reference

### Current Event Path
Check what event file is configured:
```bash
source venv/bin/activate
python -c "import os; print(os.getenv('GITHUB_EVENT_PATH', 'Not set'))"
```

### Validate Event JSON
```bash
# Check if file exists and is valid JSON
python -c "import json; print(json.load(open('test/my_pull_request.json'))['number'])"
```

### Show Event Details
```bash
# Pretty print the event JSON
python -m json.tool test/my_pull_request.json
```

## Files Created

1. **test/my_pull_request.json** - Simple template (manually edit)
2. **generate_event.py** - Script to fetch real PR data
3. **test/pr_*_event.json** - Generated from real PRs

## Next Steps

Once you have your event JSON:

1. ✅ Set `GITHUB_EVENT_PATH` in `.env`
2. ✅ Set `GITHUB_TOKEN` with repo access
3. ✅ Set `GITHUB_REPOSITORY` (format: `owner/repo`)
4. ✅ Run `./run.sh` to test locally

---

Need help? Check:
- `test/github_event_path_mock_pull_request.json` - Full example
- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request)
