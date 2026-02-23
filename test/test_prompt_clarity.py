#!/usr/bin/env python3
"""
Test script to verify prompt clarity improvements
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from core.schemas.files import FilteredFile, Patch
from core.schemas.prompts import Prompts
from core.schemas.pr_common import PRDescription
from core.schemas.files import AiSummary

# Create a sample patch
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

patch = Patch(
    start_line=20,
    end_line=26,
    patch_str=f"\n### NEW CODE TO REVIEW (lines 20-26):\n"
              f"---new_hunk---\n```\n{sample_new_hunk}\n```\n"
              f"\n### OLD CODE FOR CONTEXT (replaced code):\n"
              f"---old_hunk---\n```\n{sample_old_hunk}\n```\n"
)

# Create a filtered file
from core.schemas.patch import Patches
file = FilteredFile(
    filename="calculator.py",
    title="Test PR",
    description="Testing prompt clarity",
    file_diff="sample diff",
    additions=7,
    deletions=7,
    patches=Patches(items=[patch])
)

# Generate the review prompt
prompts = Prompts(
    summarize="",
    summarize_release_notes=""
)

ai_summary = AiSummary(
    raw_summary="Added exponential and square functions",
    short_summary="New math functions added",
    changeset_summary="Added exponential and square"
)

pr_description = PRDescription()

review_prompt = prompts.render_review_file_diff(
    file=file,
    ai_summary=ai_summary,
    pr_description=pr_description
)

print("=" * 80)
print("GENERATED REVIEW PROMPT")
print("=" * 80)
print()
print(review_prompt)
print()
print("=" * 80)
print("VERIFICATION CHECKS")
print("=" * 80)
print()

# Check for clarity markers
checks = {
    "Has 'NEW CODE TO REVIEW' header": "### NEW CODE TO REVIEW" in review_prompt,
    "Has 'OLD CODE FOR CONTEXT' header": "### OLD CODE FOR CONTEXT" in review_prompt,
    "Has line number range": "lines 20-26" in review_prompt,
    "Has critical instructions": "CRITICAL Instructions" in review_prompt,
    "Warns about old_hunk": "DO NOT REVIEW THIS" in review_prompt or "DO NOT comment on code from" in review_prompt,
    "Has reminder section": "REMINDER: Only review code in" in review_prompt,
}

for check, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"{status} {check}")

print()
if all(checks.values()):
    print("✅ All clarity checks passed!")
    print("The prompt should now be much clearer for Claude.")
else:
    print("⚠️  Some checks failed - prompt may still be ambiguous")

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
