# Before & After: Prompt Clarity Fixes

## The Problem

Claude Opus was commenting on code from `old_hunk` (removed code) instead of `new_hunk` (added code).

**Your Example:**
- **PR contained**: `exponential()` and `square()` functions (NEW CODE)
- **Claude commented on**: `logarithm()` and `natural_log()` functions (OLD CODE)

## Root Cause

The prompt didn't clearly distinguish between:
- Code to review (`new_hunk`)
- Code for context only (`old_hunk`)

---

## Fix #1: Patch Headers (core/schemas/files.py)

### BEFORE
```
---new_hunk---
```
20: def exponential(x):
21:     return math.exp(x)
```

---old_hunk---
```
def logarithm(x):
    return math.log(x)
```
```

### AFTER
```

### NEW CODE TO REVIEW (lines 20-26):
---new_hunk---
```
20: def exponential(x):
21:     return math.exp(x)
```

### OLD CODE FOR CONTEXT (replaced code):
---old_hunk---
```
def logarithm(x):
    return math.log(x)
```
```

**What changed**: Added explicit headers that label each section with its purpose.

---

## Fix #2: Critical Instructions (core/templates/prompts.py)

### BEFORE
```
## Instructions

Input: New hunks annotated with line numbers and old hunks (replaced code).
Task: Review new hunks for substantive issues.
```

### AFTER
```
## CRITICAL Instructions - READ CAREFULLY

You will see code changes in this format:
- `---new_hunk---`: The NEW CODE (what was ADDED/CHANGED) - annotated with line numbers
- `---old_hunk---`: The OLD CODE (what was REPLACED/REMOVED) - for context only

IMPORTANT: You must ONLY review and comment on the code in the `---new_hunk---` section.
Do NOT comment on code from the `---old_hunk---` section.
The old hunk is shown only to help you understand what changed.
```

**What changed**: Made instructions explicit and emphatic with warnings.

---

## Fix #3: Visual Markers in Examples (core/templates/prompts.py)

### BEFORE
```
### Example changes

---new_hunk---
```
20: def add(x, y):
21:     return x + y
```

---old_hunk---
```
def add(x, y):
    return x + y
```
```

### AFTER
```
### Example changes

---new_hunk---  ← THIS IS THE NEW CODE TO REVIEW
```
20: def add(x, y):
21:     return x + y
```

---old_hunk---  ← THIS IS OLD CODE FOR CONTEXT ONLY - DO NOT REVIEW THIS
```
def add(x, y):
    return x + y
```
```

**What changed**: Added visual arrows and explicit labels showing which section to review.

---

## Fix #4: Reminder Before Each File (core/templates/prompts.py)

### BEFORE
```
## Changes made to `calculator.py` for your review

$patches
```

### AFTER
```
## Changes made to `calculator.py` for your review

REMINDER: Only review code in `---new_hunk---` sections (with line numbers).
Ignore code in `---old_hunk---` sections (old code for context only).

$patches
```

**What changed**: Added a reminder immediately before patches to reinforce the instruction.

---

## Expected Behavior After Fixes

### Your Example PR

**What the prompt now shows:**
```

### NEW CODE TO REVIEW (lines 20-26):
---new_hunk---
```
20: def exponential(x):
21:     """Calculate e^x"""
22:     return math.exp(x)
23:
24: def square(x):
25:     """Calculate x^2"""
26:     return x * x
```

### OLD CODE FOR CONTEXT (replaced code):
---old_hunk---
```
def logarithm(x):
    """Calculate log(x)"""
    if x <= 0:
        return "Error: invalid input"
    return math.log(x)

def natural_log(x):
    return math.log(x)
```
```

**What Claude should do:**
- ✅ Comment on `exponential()` if there are issues (e.g., missing import for `math`)
- ✅ Comment on `square()` if there are issues
- ✅ Reference line numbers 20-26 only
- ❌ Should NOT comment on `logarithm()` (it's in old_hunk)
- ❌ Should NOT comment on `natural_log()` (it's in old_hunk)
- ❌ Should NOT mention "logarithm and natural_log return a string on error"

---

## Testing Your PR

1. **Run the review:**
   ```bash
   cd pr-reviewer-ai
   ./run.sh 2>&1 | tee test_fix.log
   ```

2. **Check Claude's comments:**
   - Do they mention `exponential` or `square`? ✅ Good
   - Do they mention `logarithm` or `natural_log`? ❌ Still broken

3. **If still broken, try these settings in `.env`:**
   ```bash
   # Make Claude more deterministic (less creative)
   model_temperature=0.0

   # Use Sonnet (more literal than Opus)
   heavy_model_name_claude=databricks-claude-sonnet-4-6

   # Enable debug to see full prompt
   debug=true
   ```

---

## Verification

Run this to verify the fixes are in place:
```bash
python3 verify_prompt_fix.py
```

All 8 checks should pass ✓

---

## Files Modified

1. ✅ [core/schemas/files.py](core/schemas/files.py#L111-L114) - Patch headers
2. ✅ [core/templates/prompts.py](core/templates/prompts.py#L89-L95) - Critical instructions
3. ✅ [core/templates/prompts.py](core/templates/prompts.py#L115-L128) - Visual markers
4. ✅ [core/templates/prompts.py](core/templates/prompts.py#L153-L154) - Reminder section

All fixes are now in place and verified ✓
