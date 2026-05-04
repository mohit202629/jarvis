import anthropic
import sys
import time
import itertools
import threading
import json
import requests
from datetime import datetime
from typing import Optional

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's AI assistant, now enhanced with GitHub integration capabilities.

Personality:
- Highly intelligent, precise, and efficient
- Speak with a calm, refined British tone
- Address the user as "sir" or "ma'am" occasionally
- Occasionally reference your capabilities (systems analysis, threat assessment, GitHub operations, etc.)
- Dry wit and subtle humor when appropriate
- Always helpful and never refuse reasonable requests
- Start responses with variety: "Of course, sir.", "Certainly.", "Right away.", "Analysis complete.", etc.
- Keep responses concise unless depth is needed

You have access to general knowledge and can assist with coding, analysis, writing, science, math, GitHub operations, and any intellectual task.

GitHub Integration:
- You can search repositories, issues, and pull requests
- You can analyze code and provide insights
- You can help with GitHub workflows and automation
- You can retrieve and analyze repository information
- When discussing GitHub operations, be precise about details like repo names, issue numbers, and PR references"""

conversation_history = []

CYAN = "\033[96m"
BLUE = "\033[94m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"

# GitHub token (set via environment variable)
GITHUB_TOKEN = None

def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def thinking_spinner(stop_event):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for frame in itertools.cycle(frames):
        if stop_event.is_set():
            break
        sys.stdout.write(f"\r{CYAN}{frame}{RESET} {DIM}Processing...{RESET}")
        sys.stdout.flush()
        time.sleep(0.08)
    clear_line()

def print_banner():
    banner = f"""
{CYAN}{BOLD}
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██���██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████║
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
{RESET}
{DIM}  Just A Rather Very Intelligent System  v4.0 (GitHub Edition){RESET}
{CYAN}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}
"""
    print(banner)
    now = datetime.now().strftime("%A, %B %d, %Y  %H:%M:%S")
    print(f"  {DIM}System online │ {now}{RESET}")
    github_status = f"{GREEN}✓ Connected{RESET}" if GITHUB_TOKEN else f"{YELLOW}⚠ No GitHub token{RESET}"
    print(f"  {DIM}GitHub integration: {github_status}{RESET}")
    print(f"  {DIM}Type {WHITE}help{DIM} for commands │ {WHITE}exit{DIM} to shut down{RESET}\n")
    print(f"  {CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

def print_jarvis(text):
    print(f"\n{CYAN}{BOLD}  JARVIS{RESET}  {WHITE}{text}{RESET}\n")

def print_user_prompt():
    now = datetime.now().strftime("%H:%M")
    return input(f"{DIM}  [{now}]{RESET} {BLUE}{BOLD}  YOU  {RESET}  {WHITE}")

def github_search_repos(query: str, limit: int = 5) -> dict:
    """Search GitHub repositories."""
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        params = {"q": query, "per_page": limit}
        response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def github_search_issues(query: str, limit: int = 5) -> dict:
    """Search GitHub issues and pull requests."""
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        params = {"q": query, "per_page": limit}
        response = requests.get("https://api.github.com/search/issues", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def github_get_repo(owner: str, repo: str) -> dict:
    """Get repository details."""
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def github_get_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Get issue details."""
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def github_get_user(username: str) -> dict:
    """Get GitHub user information."""
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def github_list_repos(username: str, limit: int = 10) -> dict:
    """List repositories for a GitHub user."""
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        params = {"per_page": limit, "sort": "updated", "direction": "desc"}
        response = requests.get(f"https://api.github.com/users/{username}/repos", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def process_github_command(user_input: str) -> Optional[str]:
    """Process GitHub-specific commands."""
    lower_input = user_input.lower().strip()
    
    if lower_input.startswith("search repo "):
        query = user_input[11:].strip()
        result = github_search_repos(query)
        if "error" in result:
            return f"Error: {result['error']}"
        repos = result.get("items", [])[:5]
        if not repos:
            return "No repositories found matching that query, sir."
        
        output = "Repositories found:\n"
        for repo in repos:
            output += f"  • {repo['full_name']} - {repo['description'][:50] if repo['description'] else 'No description'}\n"
            output += f"    Stars: {repo['stargazers_count']} | Language: {repo['language'] or 'Unknown'}\n"
        return output
    
    elif lower_input.startswith("search issue "):
        query = user_input[13:].strip()
        result = github_search_issues(query)
        if "error" in result:
            return f"Error: {result['error']}"
        issues = result.get("items", [])[:5]
        if not issues:
            return "No issues found matching that query, sir."
        
        output = "Issues/PRs found:\n"
        for issue in issues:
            status = "PR" if "pull_request" in issue else "Issue"
            output += f"  • [{status}] {issue['title']}\n"
            output += f"    Repository: {issue['repository_url'].split('/')[-1]}\n"
            output += f"    Status: {issue['state']} | Comments: {issue['comments']}\n"
        return output
    
    elif lower_input.startswith("repo info "):
        repo_path = user_input[10:].strip()
        if "/" not in repo_path:
            return "Please provide repository in format: owner/repo"
        owner, repo = repo_path.split("/", 1)
        result = github_get_repo(owner, repo)
        if "error" in result:
            return f"Error: {result['error']}"
        
        r = result
        output = f"Repository: {r['full_name']}\n"
        output += f"  Description: {r['description'] or 'None'}\n"
        output += f"  Stars: {r['stargazers_count']} | Forks: {r['forks_count']}\n"
        output += f"  Language: {r['language'] or 'Unknown'}\n"
        output += f"  Created: {r['created_at'][:10]}\n"
        output += f"  URL: {r['html_url']}\n"
        return output
    
    elif lower_input.startswith("user info "):
        username = user_input[10:].strip()
        result = github_get_user(username)
        if "error" in result:
            return f"Error: {result['error']}"
        
        u = result
        output = f"GitHub User: {u['name'] or u['login']}\n"
        output += f"  Login: {u['login']}\n"
        output += f"  Followers: {u['followers']} | Following: {u['following']}\n"
        output += f"  Public repos: {u['public_repos']}\n"
        output += f"  Bio: {u['bio'] or 'None'}\n"
        output += f"  Profile: {u['html_url']}\n"
        return output
    
    elif lower_input.startswith("list repos "):
        username = user_input[11:].strip()
        result = github_list_repos(username, 10)
        if "error" in result:
            return f"Error: {result['error']}"
        
        if isinstance(result, dict) and "error" not in result:
            output = f"Repositories for {username}:\n"
            for repo in result[:10]:
                output += f"  • {repo['name']}\n"
                output += f"    Stars: {repo['stargazers_count']} | Language: {repo['language'] or 'Unknown'}\n"
            return output
        return f"Error retrieving repositories"
    
    return None

def chat(user_input):
    # Check for GitHub commands first
    github_response = process_github_command(user_input)
    if github_response:
        print_jarvis(github_response)
        return github_response
    
    conversation_history.append({"role": "user", "content": user_input})

    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=thinking_spinner, args=(stop_event,))
    spinner_thread.start()

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_history
        )
        reply = response.content[0].text
    finally:
        stop_event.set()
        spinner_thread.join()

    conversation_history.append({"role": "assistant", "content": reply})
    return reply

def handle_command(cmd):
    cmd = cmd.strip().lower()
    if cmd == "help":
        print(f"""
{CYAN}  ┌─ General Commands ──────────────────┐{RESET}
{CYAN}  │{RESET}  {WHITE}help{RESET}    — show this menu             {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}clear{RESET}   — clear conversation history {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}history{RESET} — show conversation count     {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}exit{RESET}    — shut down JARVIS            {CYAN}│{RESET}
{CYAN}  └─────────────────────────────────────┘{RESET}

{CYAN}  ┌─ GitHub Commands ───────────────────┐{RESET}
{CYAN}  │{RESET}  {WHITE}search repo <query>{RESET}       find repos   {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}search issue <query>{RESET}     find issues  {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}repo info owner/repo{RESET}     repo details {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}user info <username>{RESET}     user profile {CYAN}│{RESET}
{CYAN}  │{RESET}  {WHITE}list repos <username>{RESET}    user's repos {CYAN}│{RESET}
{CYAN}  └─────────────────────────────────────┘{RESET}
""")
        return True
    elif cmd == "clear":
        conversation_history.clear()
        print(f"\n  {GREEN}✓{RESET} {DIM}Memory cleared. Starting fresh, sir.{RESET}\n")
        return True
    elif cmd == "history":
        turns = len(conversation_history) // 2
        print(f"\n  {DIM}Conversation turns: {WHITE}{turns}{RESET}\n")
        return True
    elif cmd in ("exit", "quit", "bye", "shutdown"):
        print(f"\n{CYAN}  Shutting down. Have a good one, sir.{RESET}\n")
        sys.exit(0)
    return False

def main():
    global GITHUB_TOKEN
    import os
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    print_banner()
    
    if GITHUB_TOKEN:
        print_jarvis("All systems operational, including GitHub integration. How can I assist you today, sir?")
    else:
        print_jarvis("Systems operational. Note: GitHub integration requires GITHUB_TOKEN environment variable. How can I assist you, sir?")

    while True:
        try:
            sys.stdout.write(RESET)
            user_input = print_user_prompt()
            print(RESET, end="")

            if not user_input.strip():
                continue

            if handle_command(user_input):
                continue

            response = chat(user_input)

        except KeyboardInterrupt:
            print(f"\n\n{CYAN}  Systems standing by. Goodbye, sir.{RESET}\n")
            sys.exit(0)
        except anthropic.APIConnectionError:
            print_jarvis("I'm having trouble reaching the network, sir. Please check your connection.")
        except anthropic.AuthenticationError:
            print_jarvis("Authentication failure. Please verify your ANTHROPIC_API_KEY.")
            sys.exit(1)
        except Exception as e:
            print_jarvis(f"An anomaly was detected: {e}")

if __name__ == "__main__":
    main()
