# Fix Summary: Claude Commenting on Wrong Code

## Problem Identified

Claude was commenting on code from the `old_hunk` (removed/replaced code) instead of the `new_hunk` (added/changed code).

**Example:**
- **PR contained**: `exponential()` and `square()` functions (NEW CODE)
- **Claude commented on**: `logarithm()` and `natural_log()` functions (OLD CODE)

## Root Cause

The prompt format was ambiguous. Claude couldn't clearly distinguish between:
- Code to review (new_hunk)
- Code for context only (old_hunk)

## Fixes Applied

### 1. **Improved Instructions** (`core/templates/prompts.py`)

**Before:**
```
Input: New hunks annotated with line numbers and old hunks (replaced code).
Task: Review new hunks for substantive issues.
```

**After:**
```
CRITICAL Instructions - READ CAREFULLY

You will see code changes in this format:
- `---new_hunk---`: The NEW CODE (what was ADDED/CHANGED) - annotated with line numbers
- `---old_hunk---`: The OLD CODE (what was REPLACED/REMOVED) - for context only

IMPORTANT: You must ONLY review and comment on the code in the `---new_hunk---` section.
Do NOT comment on code from the `---old_hunk---` section.
```

### 2. **Enhanced Example** (`core/templates/prompts.py`)

**Before:**
```
---new_hunk - --
```
(no explanation)

**After:**
```
---new_hunk---  ← THIS IS THE NEW CODE TO REVIEW
---old_hunk---  ← THIS IS OLD CODE FOR CONTEXT ONLY - DO NOT REVIEW THIS
```

### 3. **Added Reminder Section** (`core/templates/prompts.py`)

Added before each file review:
```
REMINDER: Only review code in `---new_hunk---` sections (with line numbers).
Ignore code in `---old_hunk---` sections (old code for context only).
```

### 4. **Clearer Patch Headers** (`core/schemas/files.py`)

**Before:**
```
---new_hunk---
```

**After:**
```
### NEW CODE TO REVIEW (lines 20-26):
---new_hunk---
...
### OLD CODE FOR CONTEXT (replaced code):
---old_hunk---
```

## Testing the Fix

### Test 1: Verify Prompt Format
```bash
cd pr-reviewer-ai
source venv/bin/activate
python test_prompt_clarity.py
```

Expected output: All clarity checks should pass ✓

### Test 2: Run Review with Debug
```bash
# Enable debug mode
echo "debug=true" >> .env

# Run review
./run.sh 2>&1 | tee test_review.log

# Check what Claude receives
grep -A 100 "PROMPT START" test_review.log
```

### Test 3: Create Simple Test PR
1. Create a PR with ONE file, ONE function change
2. Run the reviewer
3. Verify Claude comments on the NEW code, not OLD code

## Expected Improvements

✅ **Claude should now**:
- Only comment on code in `---new_hunk---` sections
- Ignore code in `---old_hunk---` sections
- Reference correct line numbers from the new code
- Focus on actual changes made in the PR

❌ **Claude should NOT**:
- Comment on removed/replaced code
- Reference functions from old_hunk
- Mix up old and new code
- Invent code that doesn't exist in new_hunk

## If Issue Persists

If Claude still comments on wrong code after these fixes:

### 1. Check Model Settings
```bash
# Try Sonnet (more literal, less creative)
echo "heavy_model_name_claude=databricks-claude-sonnet-4-6" >> .env

# Lower temperature (more deterministic)
echo "model_temperature=0.0" >> .env
```

### 2. Verify Patch Extraction
```bash
python debug_review.py
```

Look at "Patch Content" - verify it matches your actual PR changes.

### 3. Check Token Limits
```bash
# Reduce batch size
echo "max_files=5" >> .env
```

### 4. Simplify PR
- Break large PRs into smaller chunks
- Review one file at a time
- Avoid mixing multiple types of changes

## Files Modified

1. **core/templates/prompts.py** - Clearer instructions and examples
2. **core/schemas/files.py** - Better patch headers
3. **core/bots/bot_claude.py** - Enhanced debug logging (from earlier)
4. **test_prompt_clarity.py** - NEW - Test script
5. **debug_review.py** - NEW - Diagnostic tool (from earlier)

## Rollback Instructions

If these changes cause any issues, revert with:
```bash
git checkout core/templates/prompts.py
git checkout core/schemas/files.py
```

## Next Steps

1. ✅ Test with your actual PR
2. ✅ Verify Claude comments are now correct
3. ✅ If still wrong, run diagnostics and share output
4. ✅ Consider model settings (Sonnet vs Opus, temperature)

---

**Status**: ✅ Fix Applied
**Date**: 2026-02-23
**Files Changed**: 2 core files + 2 test/debug scripts
