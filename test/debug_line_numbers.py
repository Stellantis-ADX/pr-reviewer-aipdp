#!/usr/bin/env python3
"""
Debug script to check line number mapping in patches
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from core.schemas.pr_common import PRInfo
from core.review.code import generate_filtered_ignored_files
from core.schemas.options import Options

# Initialize
options = Options(debug=True, disable_review=False, disable_release_notes=False)
pr_info = PRInfo()

# Get filtered files
filtered_files, _ = generate_filtered_ignored_files(pr_info, options)

print("=" * 100)
print("LINE NUMBER MAPPING DIAGNOSTICS")
print("=" * 100)
print()

for file in filtered_files:
    if file.filename != "calculator.py":
        continue

    print(f"\n{'='*100}")
    print(f"FILE: {file.filename}")
    print(f"{'='*100}\n")

    for i, patch in enumerate(file.patches.items):
        print(f"\n{'-'*100}")
        print(f"PATCH #{i+1}")
        print(f"{'-'*100}")
        print(f"Start Line: {patch.start_line}")
        print(f"End Line: {patch.end_line}")
        print(f"Line Range: {patch.start_line}-{patch.end_line} ({patch.end_line - patch.start_line + 1} lines)")
        print()

        # Show the actual patch content with line numbers
        print("PATCH CONTENT SHOWN TO CLAUDE:")
        print("-" * 100)
        lines = patch.patch_str.split('\n')
        for line_no, line in enumerate(lines[:80], 1):  # First 80 lines
            print(f"{line}")
        if len(lines) > 80:
            print(f"... ({len(lines) - 80} more lines)")
        print()

        # Try to extract the actual function definitions
        print("FUNCTIONS IN THIS PATCH:")
        print("-" * 100)
        in_new_hunk = False
        for line in lines:
            if '---new_hunk---' in line:
                in_new_hunk = True
                continue
            if '---old_hunk---' in line:
                in_new_hunk = False
                continue
            if in_new_hunk and 'def ' in line:
                # Extract line number and function name
                if ':' in line and 'def ' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2 and parts[0].strip().isdigit():
                        line_num = parts[0].strip()
                        func_line = parts[1].strip()
                        if 'def ' in func_line:
                            func_name = func_line.split('(')[0].replace('def ', '')
                            print(f"  Line {line_num}: {func_name}")

print("\n" + "=" * 100)
print("ANALYSIS:")
print("=" * 100)
print("""
The line numbers shown to Claude should match the actual line numbers in the GitHub file.
If they don't match, comments will be posted to the wrong lines.

To verify:
1. Check the GitHub PR and find the actual line numbers for functions
2. Compare with the line numbers shown in "PATCH CONTENT" above
3. If there's a mismatch, the patch extraction is calculating wrong line numbers

Common issues:
- Diff header parsing: @@ -old_start,old_count +new_start,new_count @@
- Line number calculation in parse_patch() function
- Multiple patches with overlapping ranges
""")
