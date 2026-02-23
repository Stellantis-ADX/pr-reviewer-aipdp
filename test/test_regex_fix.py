#!/usr/bin/env python3
"""
Test the regex fix for line number parsing
"""
import re

# Old regex (didn't work with spaces)
old_regex = r"(?:^|\s)(\d+)-(\d+):\s*$"

# New regex (allows spaces around hyphen)
new_regex = r"(?:^|\s)(\d+)\s*-\s*(\d+):\s*$"

# Test cases - formats that Claude generates
test_cases = [
    "63 - 65:",      # With spaces (Claude's actual output)
    "8 - 9:",        # With spaces
    "22 - 22:",      # Example from prompt
    "63-65:",        # Without spaces (also valid)
    "100-200:",      # Without spaces
    "  63 - 65:",    # With leading spaces
    "\t100-200:",    # With leading tab
]

print("=" * 80)
print("REGEX FIX VERIFICATION")
print("=" * 80)
print()

print("Old Regex (broken):", old_regex)
print("New Regex (fixed): ", new_regex)
print()

print("-" * 80)
print("Test Results:")
print("-" * 80)

all_passed = True
for test in test_cases:
    old_match = bool(re.search(old_regex, test))
    new_match = bool(re.search(new_regex, test))

    # Extract line numbers with new regex
    if new_match:
        match = re.search(new_regex, test)
        start_line = match.group(1)
        end_line = match.group(2)
        result = f"✓ Parsed as {start_line}-{end_line}"
    else:
        result = "✗ Failed to parse"
        all_passed = False

    print(f"Input: '{test}'")
    print(f"  Old regex: {'✓ Match' if old_match else '✗ No match'}")
    print(f"  New regex: {result}")
    print()

print("-" * 80)
if all_passed:
    print("✅ All test cases passed!")
    print("The new regex correctly handles spaces around the hyphen.")
else:
    print("⚠️  Some test cases failed")

print()
print("=" * 80)
print("EXPECTED BEHAVIOR:")
print("=" * 80)
print()
print("Claude generates line numbers like: '63 - 65:'")
print("The new regex will correctly parse this format.")
print()
print("Before the fix:")
print("  - Parser couldn't find line number ranges")
print("  - Comments were not added to review buffer")
print("  - Result: 'No reviews found'")
print()
print("After the fix:")
print("  - Parser correctly identifies '63 - 65:' as a line range")
print("  - Comments are added to review buffer")
print("  - Comments get posted to GitHub PR")
