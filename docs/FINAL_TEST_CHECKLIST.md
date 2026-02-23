# Final Test Checklist

## What We Fixed

### Issue #1: Regex Parsing (FIXED ✓)
- **Problem**: Comments not being posted at all
- **Cause**: Regex expected `63-65:` but Claude generated `63 - 65:` (with spaces)
- **Fix**: Updated regex to allow optional spaces
- **File**: [core/schemas/review.py](core/schemas/review.py#L129)

### Issue #2: Line Number Mapping (FIXED ✓)
- **Problem**: Comments posted to wrong lines
- **Cause**: Context lines not annotated, causing line number confusion
- **Fix**: Always annotate ALL lines with [NEW] markers
- **Files**:
  - [core/schemas/patch.py](core/schemas/patch.py#L150-L165)
  - [core/templates/prompts.py](core/templates/prompts.py#L89-L164)

### Issue #3: Wrong Code Comments (FIXED ✓)
- **Problem**: Claude commenting on old_hunk instead of new_hunk
- **Cause**: Ambiguous prompt format
- **Fix**: Added explicit warnings and visual markers
- **File**: [core/templates/prompts.py](core/templates/prompts.py)

## Test Plan

### 1. Run the Review
```bash
cd /Users/t0142f5/Desktop/Workspace/pr-reviewer-ai/pr-reviewer-ai
./run.sh 2>&1 | tee final_test.log
```

### 2. Check the Logs
Look for:
```
✓ Found line number range: XX-XX
✓ Stored comment for line range XX-XX
✓ Submitting review for PR #2, total comments: N
```

### 3. Verify on GitHub

Go to your PR on GitHub and check:

| Function | Expected Line# | Actual Line# on GitHub | Comment About | Match? |
|----------|----------------|------------------------|---------------|--------|
| sine()   | 73             | ?                      | sine issues   | ?      |
| tangent()| 81             | ?                      | tangent issues| ?      |
| exponential() | 97        | ?                      | exponential issues | ? |

**Fill in the "?" marks by checking your actual PR.**

### 4. Expected Behavior

✅ **Line numbers in comments should match GitHub line numbers**
- If Claude says line 81, GitHub should show line 81

✅ **Comment content should match the function at that line**
- Comment on line 81 should be about `tangent()`, NOT about `exponential()`

✅ **Only NEW lines should be reviewed**
- Context lines (without `[NEW]`) should NOT have comments

## Verification Commands

### Check Debug Output
```bash
./run.sh 2>&1 | grep -A 5 "ANNOTATED NEW HUNK"
```

### Check Line Numbers in Prompt
```bash
./run.sh 2>&1 | grep "Line [0-9][0-9]*:"
```

### Check Comments Posted
```bash
./run.sh 2>&1 | grep -A 2 "Submitting review"
```

## If Issues Persist

### Issue: Line numbers still wrong

**Check:**
1. What line number does GitHub show for `def sine()`?
2. Run: `python3 test_line_mapping.py`
3. Compare output with GitHub

**If they don't match:**
- The diff header might be wrong
- File might have been edited since PR was created
- Need to investigate patch extraction

### Issue: Comments still on wrong functions

**Check:**
1. Enable debug: `echo "debug=true" >> .env`
2. Run review and save log
3. Look for what Claude sees in the prompt
4. Check if `[NEW]` markers are present

**If [NEW] markers missing:**
- Patch parsing didn't work
- Check patch format

### Issue: No comments posted

**Check:**
1. Look for "No reviews found" in log
2. Check if Claude generated comments
3. Check if regex matched line numbers

**Debug:**
```bash
./run.sh 2>&1 | grep -E "(Found line number range|No reviews found)"
```

## Success Criteria

✅ All checks passed:
- [ ] Review runs without errors
- [ ] Comments are posted to GitHub
- [ ] Line numbers match GitHub
- [ ] Comment content matches function at that line
- [ ] Only NEW code is reviewed
- [ ] Context lines are ignored

---

**Status**: Ready for Testing
**Date**: 2026-02-23
**Estimated Test Time**: 5-10 minutes
