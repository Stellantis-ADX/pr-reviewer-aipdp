#!/bin/bash
# PR Reviewer AI - Run Script

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env
if [ -f .env ]; then
    echo "Loading environment from .env..."
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found. Using .env.databricks as template..."
    if [ -f .env.databricks ]; then
        cp .env.databricks .env
        echo "Created .env from .env.databricks. Please edit it with your credentials."
        exit 1
    fi
fi

# Check required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN not set"
    exit 1
fi

if [ -z "$databricks_token" ] && [ -z "$databricks_base_url" ]; then
    echo "Warning: Databricks Claude not configured. Will use fallback bots."
fi

# Run the PR reviewer
echo "Starting PR Reviewer AI..."
python main.py

# Check exit status
if [ $? -eq 0 ]; then
    echo "✓ PR Review completed successfully"
else
    echo "✗ PR Review failed"
    exit 1
fi
