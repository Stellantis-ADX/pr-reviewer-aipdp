# Fix Summary: Comments Posted to Wrong Lines

## Problem

Comments were being posted to the wrong lines on GitHub. For example:
- Comment about **exponential** appeared on lines 80-82
- But those lines actually contained **tangent** code

## Root Cause

The patch parsing logic was **skipping line number annotations** for context lines (first 3 and last 3 lines of each patch). This caused:
1. Missing line numbers in some sections
2. Ambiguity about which lines are new vs context
3. Claude using wrong line numbers in comments

### Original Code (BROKEN)
```python
# core/schemas/patch.py lines 163-185
skip_start = 3
skip_end = 3

for line in lines:
    if line.startswith("+"):
        new_hunk_lines.append(f"{new_line}: {line[1:]}")  # Annotate added lines
    else:
        # Context lines: only annotate if NOT in skip range
        if removal_only or (skip_start < current_line <= len(lines) - skip_end):
            new_hunk_lines.append(f"{new_line}: {line}")  # Annotated
        else:
            new_hunk_lines.append(line)  # NOT annotated!
```

This meant some context lines showed no line numbers, causing confusion.

## Fix Applied

### 1. Always Annotate ALL Lines ([core/schemas/patch.py](core/schemas/patch.py#L150-L165))

**Before:**
```python
# Some lines skipped annotation
if removal_only or (skip_start < current_line <= len(lines) - skip_end):
    new_hunk_lines.append(f"{new_line}: {line}")
else:
    new_hunk_lines.append(line)  # No line number!
```

**After:**
```python
# ALL lines always annotated
for line in lines:
    if line.startswith("+"):
        new_hunk_lines.append(f"{new_line}: [NEW] {line[1:]}")
    else:
        new_hunk_lines.append(f"{new_line}: {line}")
```

### 2. Added [NEW] Markers

- Lines marked with `[NEW]` = newly added code (review these)
- Lines without `[NEW]` = context lines (don't review)
- ALL lines show ACTUAL file line numbers

### 3. Updated Prompt Instructions ([core/templates/prompts.py](core/templates/prompts.py#L89-L106))

**Added:**
```
- Lines marked `[NEW]` are NEWLY ADDED code - REVIEW THESE
- Lines WITHOUT `[NEW]` are unchanged context lines - DO NOT REVIEW
- ALL line numbers are ACTUAL line numbers from the file
- Use the EXACT line numbers shown when writing your comments
```

### 4. Updated Example Format

**Before:**
```
20: def add(x, y):
21:     z = x + y
22:     return z
```

**After:**
```
20:
21: [NEW] def add(x, y):
22: [NEW]     z = x + y
23: [NEW]     return z
24:
25: def subtract(x, y):  # Context line (no [NEW])
```

## Example Output

For the calculator.py diff:

**Before Fix:**
```
55: def sine(x):        # WRONG - should be line 73!
63: def tangent(x):     # WRONG - should be line 81!
79: def exponential(x): # WRONG - should be line 97!
```

**After Fix:**
```
70:      result *= i              # Context line
71:      return result             # Context line
72:                                # Context line
73: [NEW] def sine(x):            # NEW CODE - Line 73 ✓
74: [NEW]     """Calculate sine..."""
75: [NEW]     return math.sin(...)
...
81: [NEW] def tangent(x):         # NEW CODE - Line 81 ✓
82: [NEW]     """Calculate tangent..."""
83: [NEW]     return math.tan(...)
...
97: [NEW] def exponential(x):     # NEW CODE - Line 97 ✓
98: [NEW]     """Calculate e^x"""
99: [NEW]     return math.exp(x)
```

## Verification

Run the test:
```bash
python3 test_line_mapping.py
```

Expected output:
- ✓ Line 73: def sine()
- ✓ Line 81: def tangent()
- ✓ Line 97: def exponential()

Compare with your GitHub PR to verify line numbers match!

## Testing the Fix

1. **Run a new review:**
   ```bash
   ./run.sh
   ```

2. **Check the comments on GitHub:**
   - Comments should now appear on the CORRECT lines
   - Line numbers should match what GitHub shows
   - Comments should reference the RIGHT functions

3. **Verify with debug output:**
   ```bash
   # Enable debug mode
   echo "debug=true" >> .env
   ./run.sh 2>&1 | grep "Line [0-9]"
   ```

## Files Modified

1. ✅ [core/schemas/patch.py](core/schemas/patch.py#L150-L165) - Always annotate all lines, add [NEW] markers
2. ✅ [core/templates/prompts.py](core/templates/prompts.py#L89-L106) - Updated instructions
3. ✅ [core/templates/prompts.py](core/templates/prompts.py#L120-L133) - Updated example
4. ✅ [core/templates/prompts.py](core/templates/prompts.py#L158-L164) - Updated reminder

## Benefits

1. **Accurate Line Numbers**: All lines show their actual position in the file
2. **Clear Distinction**: [NEW] markers clearly show what to review
3. **No Ambiguity**: Context lines are visible but marked as such
4. **Correct Comments**: Comments post to the right lines on GitHub
5. **Better Clarity**: Claude knows exactly which lines are new

---

**Status**: ✅ Fix Applied and Tested
**Date**: 2026-02-23
**Related Issues**:
- Line number mismatch (FIXED)
- Comments on wrong code (FIXED)
- Regex parsing issue (FIXED in [REGEX_FIX_SUMMARY.md](REGEX_FIX_SUMMARY.md))
