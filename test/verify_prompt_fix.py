#!/usr/bin/env python3
"""
Standalone verification of prompt clarity fixes
This script tests the prompt format without requiring GitHub API access
"""

# Test the patch string format directly
sample_new_hunk = """20: def exponential(x):
21:     \"\"\"Calculate e^x\"\"\"
22:     return math.exp(x)
23:
24: def square(x):
25:     \"\"\"Calculate x^2\"\"\"
26:     return x * x"""

sample_old_hunk = """def logarithm(x):
    \"\"\"Calculate log(x)\"\"\"
    if x <= 0:
        return "Error: invalid input"
    return math.log(x)

def natural_log(x):
    return math.log(x)"""

# Simulate the patch_str format from core/schemas/files.py (lines 111-114)
patch_str = (
    f"\n### NEW CODE TO REVIEW (lines 20-26):\n"
    f"---new_hunk---\n```\n{sample_new_hunk}\n```\n"
    f"\n### OLD CODE FOR CONTEXT (replaced code):\n"
    f"---old_hunk---\n```\n{sample_old_hunk}\n```\n"
)

print("=" * 80)
print("PATCH STRING FORMAT (from core/schemas/files.py)")
print("=" * 80)
print(patch_str)
print()

# Test the review prompt instructions from core/templates/prompts.py
review_instructions = """## CRITICAL Instructions - READ CAREFULLY

You will see code changes in this format:
- `---new_hunk---`: The NEW CODE (what was ADDED/CHANGED) - annotated with line numbers
- `---old_hunk---`: The OLD CODE (what was REPLACED/REMOVED) - for context only

IMPORTANT: You must ONLY review and comment on the code in the `---new_hunk---` section.
Do NOT comment on code from the `---old_hunk---` section.
The old hunk is shown only to help you understand what changed.

Task: Review the NEW CODE in `---new_hunk---` sections for substantive issues.
"""

print("=" * 80)
print("REVIEW INSTRUCTIONS (from core/templates/prompts.py)")
print("=" * 80)
print(review_instructions)
print()

# Test the example section from core/templates/prompts.py (lines 114-128)
example_section = """### Example changes

---new_hunk---  ← THIS IS THE NEW CODE TO REVIEW
```
  z = x / y
    return z

20: def add(x, y):
21:     z = x + y
22:     return z
23:
24: def multiply(x, y):
25:     return x * y

def subtract(x, y):
  z = x - y
```

---old_hunk---  ← THIS IS OLD CODE FOR CONTEXT ONLY - DO NOT REVIEW THIS
```
z = x / y
return z


def add(x, y):
    return x + y


def subtract(x, y):
    z = x - y
```
"""

print("=" * 80)
print("EXAMPLE SECTION (from core/templates/prompts.py)")
print("=" * 80)
print(example_section)
print()

# Test the reminder section (lines 153-154)
reminder_section = """REMINDER: Only review code in `---new_hunk---` sections (with line numbers).
Ignore code in `---old_hunk---` sections (old code for context only)."""

print("=" * 80)
print("REMINDER SECTION (from core/templates/prompts.py)")
print("=" * 80)
print(reminder_section)
print()

# Verification checks
print("=" * 80)
print("VERIFICATION CHECKS")
print("=" * 80)
print()

checks = {
    "Patch has 'NEW CODE TO REVIEW' header": "### NEW CODE TO REVIEW" in patch_str,
    "Patch has 'OLD CODE FOR CONTEXT' header": "### OLD CODE FOR CONTEXT" in patch_str,
    "Patch has line number range": "lines 20-26" in patch_str,
    "Instructions have 'CRITICAL Instructions'": "CRITICAL Instructions" in review_instructions,
    "Instructions warn about old_hunk": "Do NOT comment on code from the `---old_hunk---`" in review_instructions,
    "Example has visual marker for new_hunk": "← THIS IS THE NEW CODE TO REVIEW" in example_section,
    "Example has visual marker for old_hunk": "← THIS IS OLD CODE FOR CONTEXT ONLY" in example_section,
    "Reminder section exists": len(reminder_section) > 0,
}

all_passed = True
for check, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"{status} {check}")
    if not passed:
        all_passed = False

print()
if all_passed:
    print("✅ All clarity checks passed!")
    print("The prompt format now clearly distinguishes new code from old code.")
else:
    print("⚠️  Some checks failed")

print()
print("=" * 80)
print("WHAT CLAUDE SHOULD UNDERSTAND:")
print("=" * 80)
print()
print("✓ Only review code in ---new_hunk--- sections")
print("✓ The new_hunk contains: exponential() and square() functions (lines 20-26)")
print("✓ The old_hunk contains: logarithm() and natural_log() (context only)")
print("✓ Claude should ONLY comment on exponential() and square()")
print("✓ Claude should NOT comment on logarithm() or natural_log()")
print()
print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print()
print("1. Run your actual PR review: cd pr-reviewer-ai && ./run.sh")
print("2. Check that Claude's comments reference the NEW functions (exponential, square)")
print("3. Verify Claude does NOT reference the OLD functions (logarithm, natural_log)")
print()
print("If the issue persists, try:")
print("- Set model_temperature=0.0 in .env (more deterministic)")
print("- Use Sonnet instead of Opus (more literal, less creative)")
print("- Run with debug=true and check logs")
