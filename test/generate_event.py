#!/usr/bin/env python3
"""
Generate a GitHub event JSON file from a real PR for testing locally.

Usage:
    python generate_event.py <owner>/<repo> <pr_number>
    python generate_event.py your-username/your-repo 123

Example:
    python generate_event.py octocat/Hello-World 1
"""

import json
import os
import sys
from pathlib import Path

def generate_event_json(owner_repo: str, pr_number: int):
    """Generate a GitHub event JSON from environment or create a template."""

    # Check if we have a GitHub token
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("❌ GITHUB_TOKEN not set. Creating a template instead...")
        return create_template(owner_repo, pr_number)

    try:
        from github import Github

        # Initialize GitHub API
        g = Github(github_token)

        # Get the repository
        print(f"📡 Fetching repository: {owner_repo}")
        repo = g.get_repo(owner_repo)

        # Get the pull request
        print(f"📥 Fetching PR #{pr_number}")
        pr = repo.get_pull(pr_number)

        # Build the event JSON
        event_data = {
            "action": "opened",
            "number": pr.number,
            "pull_request": {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "draft": pr.draft,
                "merged": pr.merged,
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha,
                    "repo": {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "owner": {
                            "login": repo.owner.login,
                            "type": repo.owner.type
                        },
                        "private": repo.private,
                        "html_url": repo.html_url,
                        "default_branch": repo.default_branch
                    }
                },
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha,
                    "repo": {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "owner": {
                            "login": repo.owner.login,
                            "type": repo.owner.type
                        },
                        "private": repo.private,
                        "html_url": repo.html_url
                    }
                },
                "user": {
                    "login": pr.user.login,
                    "type": pr.user.type
                },
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "commits": pr.commits,
                "html_url": pr.html_url,
                "diff_url": pr.diff_url,
                "patch_url": pr.patch_url,
                "_links": {
                    "html": {"href": pr.html_url},
                    "comments": {"href": pr.comments_url},
                    "commits": {"href": pr.commits_url}
                }
            },
            "repository": {
                "name": repo.name,
                "full_name": repo.full_name,
                "owner": {
                    "login": repo.owner.login,
                    "type": repo.owner.type
                },
                "private": repo.private,
                "html_url": repo.html_url,
                "url": repo.url,
                "default_branch": repo.default_branch
            },
            "sender": {
                "login": pr.user.login,
                "type": pr.user.type
            }
        }

        print(f"✅ Successfully fetched PR data")
        print(f"   Title: {pr.title}")
        print(f"   State: {pr.state}")
        print(f"   Changed files: {pr.changed_files}")
        print(f"   +{pr.additions} -{pr.deletions}")

        return event_data

    except Exception as e:
        print(f"❌ Error fetching PR data: {e}")
        print("Creating a template instead...")
        return create_template(owner_repo, pr_number)


def create_template(owner_repo: str, pr_number: int):
    """Create a template event JSON."""
    owner, repo = owner_repo.split("/")

    return {
        "action": "opened",
        "number": pr_number,
        "pull_request": {
            "number": pr_number,
            "title": f"PR #{pr_number} - Update Title Here",
            "body": "Update PR description here",
            "state": "open",
            "draft": False,
            "merged": False,
            "base": {
                "ref": "main",
                "sha": "abc123def456",
                "repo": {
                    "name": repo,
                    "full_name": owner_repo,
                    "owner": {
                        "login": owner,
                        "type": "User"
                    },
                    "private": False,
                    "html_url": f"https://github.com/{owner_repo}",
                    "default_branch": "main"
                }
            },
            "head": {
                "ref": "feature-branch",
                "sha": "xyz789abc012",
                "repo": {
                    "name": repo,
                    "full_name": owner_repo,
                    "owner": {
                        "login": owner,
                        "type": "User"
                    },
                    "private": False,
                    "html_url": f"https://github.com/{owner_repo}"
                }
            },
            "user": {
                "login": owner,
                "type": "User"
            },
            "additions": 50,
            "deletions": 10,
            "changed_files": 3,
            "commits": 2,
            "html_url": f"https://github.com/{owner_repo}/pull/{pr_number}",
            "diff_url": f"https://github.com/{owner_repo}/pull/{pr_number}.diff",
            "patch_url": f"https://github.com/{owner_repo}/pull/{pr_number}.patch",
            "_links": {
                "html": {"href": f"https://github.com/{owner_repo}/pull/{pr_number}"},
                "comments": {"href": f"https://api.github.com/repos/{owner_repo}/issues/{pr_number}/comments"},
                "commits": {"href": f"https://api.github.com/repos/{owner_repo}/pulls/{pr_number}/commits"}
            }
        },
        "repository": {
            "name": repo,
            "full_name": owner_repo,
            "owner": {
                "login": owner,
                "type": "User"
            },
            "private": False,
            "html_url": f"https://github.com/{owner_repo}",
            "url": f"https://api.github.com/repos/{owner_repo}",
            "default_branch": "main"
        },
        "sender": {
            "login": owner,
            "type": "User"
        }
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_event.py <owner>/<repo> <pr_number>")
        print("Example: python generate_event.py octocat/Hello-World 1")
        sys.exit(1)

    owner_repo = sys.argv[1]
    pr_number = int(sys.argv[2])

    # Validate format
    if "/" not in owner_repo:
        print("❌ Error: Repository must be in format 'owner/repo'")
        sys.exit(1)

    print(f"🔧 Generating GitHub event JSON for PR #{pr_number} in {owner_repo}")
    print()

    # Generate the event JSON
    event_data = generate_event_json(owner_repo, pr_number)

    # Save to file
    output_file = Path("test") / f"pr_{pr_number}_event.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(event_data, f, indent=2)

    print()
    print(f"✅ Event JSON saved to: {output_file}")
    print()
    print("To use this file, update your .env:")
    print(f"   GITHUB_EVENT_PATH={output_file}")
    print()
    print("Or set it directly:")
    print(f"   export GITHUB_EVENT_PATH={output_file}")


if __name__ == "__main__":
    main()
