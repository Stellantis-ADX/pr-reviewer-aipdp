#!/usr/bin/env python3
"""
Test to understand line number mapping issue
"""
import re
from core.schemas.patch import patch_start_end_line, parse_patch
from box import Box

# Example diff hunk for calculator.py scientific functions
# This is from the actual log output
sample_diff = '''@@ -68,12 +70,48 @@ def factorial(x):
     result *= i
     return result

+def sine(x):
+    """Calculate sine of x (in degrees)"""
+    return math.sin(math.radians(x))
+
+def cosine(x):
+    """Calculate cosine of x (in degrees)"""
+    return math.cos(math.radians(x))
+
+def tangent(x):
+    """Calculate tangent of x (in degrees)"""
+    return math.tan(math.radians(x))
+
+def logarithm(x):
+    """Calculate logarithm base 10 of x"""
+    if x <= 0:
+        return "Error: Logarithm not defined for non-positive numbers"
+    return math.log10(x)
+
+def natural_log(x):
+    """Calculate natural logarithm (ln) of x"""
+    if x <= 0:
+        return "Error: Natural log not defined for non-positive numbers"
+    return math.log(x)
+
+def exponential(x):
+    """Calculate e^x"""
+    return math.exp(x)
+
+def square(x):
+    """Calculate x squared"""
+    return x ** 2
+
+def cube(x):
+    """Calculate x cubed"""
+    return x ** 3
+
 def main():
     """Main calculator function"""
-    print("=" * 50)
-    print("Advanced Calculator")
-    print("=" * 50)
-    print("\\nOperations:")
+    print("=" * 60)
+    print("Advanced Scientific Calculator")
+    print("=" * 60)
+    print("\\nBasic Operations:")
     print("1. Add (+)")
     print("2. Subtract (-)")
     print("3. Multiply (*)")
'''

print("=" * 100)
print("LINE NUMBER MAPPING TEST")
print("=" * 100)
print()

# Extract line numbers from diff header
patch_lines = patch_start_end_line(sample_diff)
if not patch_lines:
    print("ERROR: Could not parse diff header!")
    exit(1)

patch_lines_box = Box(patch_lines)

print("DIFF HEADER ANALYSIS:")
print("-" * 100)
print(f"Diff header: @@ -68,12 +70,48 @@")
print()
print(f"Old file:")
print(f"  Start line: {patch_lines_box.old_hunk.start_line}")
print(f"  End line:   {patch_lines_box.old_hunk.end_line}")
print()
print(f"New file (THIS IS WHAT MATTERS):")
print(f"  Start line: {patch_lines_box.new_hunk.start_line}")
print(f"  End line:   {patch_lines_box.new_hunk.end_line}")
print()
print(f"Expected: New functions should start around line {patch_lines_box.new_hunk.start_line}")
print()

# Parse the patch to see what line numbers get annotated
hunks = parse_patch(sample_diff, patch_lines_box)

print("=" * 100)
print("ANNOTATED NEW HUNK (what Claude sees):")
print("=" * 100)
print()

new_hunk_lines = hunks['new_hunk'].split('\n')
for i, line in enumerate(new_hunk_lines[:50], 1):  # First 50 lines
    print(line)
    if 'def sine' in line or 'def tangent' in line or 'def exponential' in line:
        print(f"  ^^^ FOUND FUNCTION ^^^")

print()
print("=" * 100)
print("FUNCTION LINE NUMBERS:")
print("=" * 100)
print()

# Extract function line numbers
for line in new_hunk_lines:
    if ': def ' in line:
        parts = line.split(':', 1)
        if parts[0].strip().isdigit():
            line_num = parts[0].strip()
            func_name = parts[1].split('(')[0].replace('def', '').strip()
            print(f"Line {line_num}: def {func_name}()")

print()
print("=" * 100)
print("DIAGNOSIS:")
print("=" * 100)
print()
print(f"The diff says new content starts at line {patch_lines_box.new_hunk.start_line}")
print()
print("Check if the annotated line numbers above match:")
print("1. Go to your GitHub PR")
print("2. Look at the 'Files changed' tab")
print("3. Find the calculator.py file")
print("4. Check what line numbers GitHub shows for def sine(), def tangent(), def exponential()")
print()
print("If the line numbers DON'T match, there's a bug in the patch parsing.")
print("If they DO match, the issue is in how comments are posted to GitHub.")
