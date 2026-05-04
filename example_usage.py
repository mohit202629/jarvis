#!/usr/bin/env python3
"""Example usage of JARVIS GitHub API functions."""

import os
from jarvis_github import (
    github_search_repos,
    github_get_repo,
    github_get_user,
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    print("Error: Set GITHUB_TOKEN environment variable first")
    exit(1)

print("\n=== Example 1: Search Repos ===")
result = github_search_repos("python machine learning", limit=3)
if "items" in result:
    for repo in result["items"][:3]:
        print(f"• {repo['full_name']} - {repo['stargazers_count']} stars")

print("\n=== Example 2: Get Repo Info ===")
repo = github_get_repo("facebook", "react")
print(f"Repository: {repo['full_name']}")
print(f"Stars: {repo['stargazers_count']}")
print(f"Language: {repo['language']}")

print("\n=== Example 3: Get User Info ===")
user = github_get_user("torvalds")
print(f"User: {user['name']}")
print(f"Followers: {user['followers']}")
print(f"Public Repos: {user['public_repos']}")
