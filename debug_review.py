#!/usr/bin/env python3
"""
Debug script to diagnose review issues
Shows what prompts are sent to Claude and what responses are received
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.schemas.options import Options
from core.schemas.prompts import Prompts
from core.schemas.pr_common import PRInfo, PRDescription
from core.schemas.files import FilteredFile, AiSummary
from core.review.code import generate_filtered_ignored_files
from core.utils import get_input_default, string_to_bool
from core.consts import ACTION_INPUTS

def main():
    print("=" * 70)
    print("DEBUG: PR Review Diagnostic Tool")
    print("=" * 70)
    print()

    # Get options
    options = Options(
        debug=True,
        disable_review=False,
        disable_release_notes=False,
        databricks_base_url=os.getenv("databricks_base_url"),
        databricks_token=os.getenv("databricks_token"),
        light_model_name_claude=os.getenv("light_model_name_claude", "claude-sonnet-4-5"),
        heavy_model_name_claude=os.getenv("heavy_model_name_claude", "claude-opus-4-6"),
    )

    print(f"✓ Databricks URL: {options.databricks_base_url}")
    print(f"✓ Light model: {options.light_model_name_claude}")
    print(f"✓ Heavy model: {options.heavy_model_name_claude}")
    print()

    # Get PR info
    pr_info = PRInfo()
    pr_description = PRDescription()

    print(f"✓ PR #{pr_info.number}: {pr_info.title}")
    print(f"✓ Base: {pr_info.base_sha[:8]} -> Head: {pr_info.head_sha[:8]}")
    print()

    # Get filtered files
    filtered_files, ignored_files = generate_filtered_ignored_files(pr_info, options)

    print(f"✓ Files to review: {len(filtered_files)}")
    print(f"✓ Files ignored: {len(ignored_files)}")
    print()

    if not filtered_files:
        print("❌ No files to review!")
        return

    # Show first file details
    file = filtered_files[0]
    print(f"📄 Analyzing first file: {file.filename}")
    print(f"   Lines changed: +{file.additions} -{file.deletions}")
    print(f"   Number of patches: {len(file.patches)}")
    print()

    # Show patches
    for i, patch in enumerate(file.patches.items[:3]):  # Show first 3 patches
        print(f"   Patch {i+1}:")
        print(f"   Lines {patch.start_line}-{patch.end_line}")
        print(f"   Tokens: {patch.tokens}")
        print()
        print("   --- Patch Content ---")
        print(patch.patch_str[:500])
        print("   --- End Patch ---")
        print()

    # Create a fake AI summary for testing
    ai_summary = AiSummary(
        raw_summary="Test PR changes",
        short_summary="Testing code review",
        changeset_summary="Modified test files"
    )

    # Generate the review prompt
    prompts = Prompts(
        summarize="",
        summarize_release_notes=""
    )

    review_prompt = prompts.render_review_file_diff(
        file=file,
        ai_summary=ai_summary,
        pr_description=pr_description
    )

    print("=" * 70)
    print("REVIEW PROMPT BEING SENT TO CLAUDE")
    print("=" * 70)
    print()
    print(review_prompt[:2000])
    print()
    print(f"... (showing first 2000 of {len(review_prompt)} characters)")
    print()
    print(f"💡 Total prompt length: {len(review_prompt)} characters")
    print(f"💡 Total prompt tokens (estimated): {len(review_prompt) // 4}")
    print()

    # Check if prompt is too long
    if len(review_prompt) > options.heavy_token_limits.request_tokens * 4:
        print("⚠️  WARNING: Prompt may be too long for the model!")
        print(f"   Max tokens: {options.heavy_token_limits.request_tokens}")
        print(f"   Estimated tokens: {len(review_prompt) // 4}")
        print()

    print("=" * 70)
    print("To run full review with debug output:")
    print("  cd pr-reviewer-ai && ./run.sh 2>&1 | tee review_debug.log")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
