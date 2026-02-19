#!/usr/bin/env python3
"""
Quick test script to verify Databricks Claude bot connection
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.bots.bot_claude import ClaudeBot, ClaudeOptions
from core.schemas.options import Options
from core.schemas.limits import TokenLimits

def test_claude_bot():
    print("=" * 60)
    print("Testing Databricks Claude Bot Connection")
    print("=" * 60)

    # Get configuration from environment
    databricks_base_url = os.getenv("databricks_base_url")
    databricks_token = os.getenv("databricks_token")
    light_model = os.getenv("light_model_name_claude", "claude-sonnet-4-5")

    print(f"\nConfiguration:")
    print(f"  Base URL: {databricks_base_url}")
    print(f"  Token: {'*' * 20 if databricks_token else 'NOT SET'}")
    print(f"  Model: {light_model}")

    if not databricks_base_url or not databricks_token:
        print("\n❌ Error: Databricks credentials not configured!")
        print("Please set databricks_base_url and databricks_token in .env")
        return False

    try:
        # Create a minimal Options object
        options = Options(
            debug=True,
            disable_review=False,
            disable_release_notes=False,
            system_message="You are a helpful AI assistant.",
        )

        # Create Claude bot
        print(f"\n📡 Creating Claude bot...")
        claude_bot = ClaudeBot(
            options=options,
            claude_options=ClaudeOptions(
                model=light_model,
                token_limits=TokenLimits(light_model)
            ),
            api_key=databricks_token,
            base_url=databricks_base_url
        )

        print("✓ Bot created successfully")

        # Test a simple chat
        print(f"\n💬 Testing chat with model: {light_model}")
        print("   Sending: 'Say hello in one sentence'")

        response = claude_bot.chat("Say hello in one sentence")

        if response and response.message:
            print(f"\n✓ Response received:")
            print(f"   {response.message}")
            print(f"\n✅ SUCCESS! Databricks Claude bot is working correctly.")
            return True
        else:
            print(f"\n❌ Error: Empty response from bot")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_claude_bot()
    sys.exit(0 if success else 1)
