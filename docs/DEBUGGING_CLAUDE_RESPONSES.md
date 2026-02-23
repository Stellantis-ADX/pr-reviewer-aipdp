# Debugging Claude Review Issues

## Problem: Claude Comments on Wrong/Different Code

If Claude Opus is commenting on code that doesn't match your PR, follow these steps:

## Step 1: Enable Debug Mode

Edit your `.env` file:
```bash
debug=true
```

This will show:
- Full prompts sent to Claude (first 5000 chars)
- Full responses from Claude (first 3000 chars)
- Token usage
- API call timings

## Step 2: Run the Diagnostic Tool

```bash
cd pr-reviewer-ai
source venv/bin/activate
python debug_review.py
```

This shows:
- What files are being reviewed
- The exact patches being extracted
- The prompt structure
- Token counts

## Step 3: Run Review with Full Logging

```bash
./run.sh 2>&1 | tee review_debug.log
```

This saves all output to `review_debug.log` for analysis.

## Common Causes & Fixes

### 1. ❌ Prompt Too Long (Token Limit Exceeded)

**Symptoms:**
- Comments reference code not in the diff
- Truncated or incomplete reviews
- Random code snippets

**Check:**
```bash
python debug_review.py | grep "WARNING: Prompt may be too long"
```

**Fix:**
Reduce `max_files` in `.env`:
```bash
max_files=10  # Instead of 150
```

Or split large files into smaller changes.

### 2. ❌ Multiple Hunks Confusion

**Symptoms:**
- Claude mixes up different sections of the same file
- Comments reference earlier/later code sections

**Check:**
Look for multiple patches in debug output:
```bash
python debug_review.py | grep "Number of patches"
```

**Fix:**
This is usually a model issue. The prompt already includes clear hunk separators. Try:
1. Use Sonnet instead of Opus for that file
2. Break PR into smaller chunks
3. Add more context in PR description

### 3. ❌ Patch Extraction Error

**Symptoms:**
- Code in comments doesn't match PR at all
- Line numbers are way off

**Check:**
```bash
python debug_review.py
```

Look at "Patch Content" sections. Verify they match your actual PR changes.

**Fix:**
If patches look wrong, this is a bug. Check:
- File encoding issues (non-UTF8)
- Binary files mistakenly being reviewed
- Very large diffs (>1000 lines)

### 4. ❌ Model Hallucination

**Symptoms:**
- Claude invents code that doesn't exist
- References functions/classes not in the PR
- Suggests changes to unchanged files

**Fix:**
This is a model behavior issue. Try:
1. **More specific PR description**:
   ```
   Changes ONLY to calculate() function in math.py
   No changes to other files or functions
   ```

2. **Adjust temperature** (make it more deterministic):
   ```bash
   model_temperature=0.0  # Instead of 0.2
   ```

3. **Use Sonnet** for initial reviews:
   ```bash
   heavy_model_name_claude=databricks-claude-sonnet-4-6
   ```
   Sonnet is less creative, more literal.

### 5. ❌ Context Window Issues

**Symptoms:**
- Early files reviewed correctly
- Later files have wrong comments
- Review quality degrades over time

**Fix:**
Each file is reviewed independently, so this shouldn't happen. But if it does:
```bash
# Review files in smaller batches
max_files=5
```

## Advanced Debugging

### View Exact Prompt Sent to Claude

```bash
./run.sh 2>&1 | grep -A 200 "PROMPT START"
```

### View Exact Response from Claude

```bash
./run.sh 2>&1 | grep -A 100 "RESPONSE START"
```

### Check Token Usage

```bash
./run.sh 2>&1 | grep "tokens:"
```

### Isolate One File

1. Create a PR with only one file
2. Run review with debug mode
3. Check if the issue persists

## Model-Specific Issues

### Claude Opus vs Sonnet

**Opus** (claude-opus-4-6):
- More powerful, better reasoning
- Sometimes "too creative" - may infer things
- Higher token limit (16k response)

**Sonnet** (claude-sonnet-4-5):
- Faster, more literal
- Sticks closer to what's actually there
- Lower token limit (8k response)

**Test with Sonnet:**
```bash
# In .env
heavy_model_name_claude=databricks-claude-sonnet-4-6
```

If Sonnet gives correct comments but Opus doesn't, it's a model behavior issue.

## Report the Issue

If you've tried everything and the issue persists, gather this info:

1. **Debug output:**
   ```bash
   python debug_review.py > debug_output.txt
   ```

2. **Review log:**
   ```bash
   ./run.sh 2>&1 | tee review.log
   ```

3. **What's in your PR:**
   - File name
   - Actual code changed (first 50 lines)

4. **What Claude said:**
   - The comment it made
   - Line numbers it referenced

5. **Example:**
   ```
   PR changes: Added line "print('hello')" to line 5 of test.py
   Claude said: "Remove the console.log() on line 20"
   Problem: There is no console.log on line 20, and this is Python not JavaScript
   ```

## Quick Fixes to Try Now

```bash
# 1. Lower temperature (less creative)
echo "model_temperature=0.0" >> .env

# 2. Use Sonnet instead
echo "heavy_model_name_claude=databricks-claude-sonnet-4-6" >> .env

# 3. Reduce batch size
echo "max_files=5" >> .env

# 4. Run with debug
echo "debug=true" >> .env

# 5. Test
./run.sh 2>&1 | tee test.log
```

## Verify Patch Extraction

Create this test script `test_patch.py`:
```python
from core.schemas.pr_common import PRInfo
from core.review.code import generate_filtered_ignored_files
from core.schemas.options import Options
import os
from dotenv import load_dotenv

load_dotenv()

options = Options(debug=True, disable_review=False, disable_release_notes=False)
pr_info = PRInfo()
filtered_files, _ = generate_filtered_ignored_files(pr_info, options)

for file in filtered_files:
    print(f"\nFile: {file.filename}")
    for i, patch in enumerate(file.patches.items):
        print(f"\nPatch {i+1} (lines {patch.start_line}-{patch.end_line}):")
        print(patch.patch_str)
```

Run it:
```bash
source venv/bin/activate
python test_patch.py
```

Compare output with your actual PR diff on GitHub.

---

**Need more help?** Share:
- Output of `debug_review.py`
- The problematic comment Claude made
- What the actual code change was
