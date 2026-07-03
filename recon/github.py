# -*- coding: utf-8 -*-
"""
GitHub repository & secret dorking scanner.
"""

import random
import urllib.parse

try:
    import requests
except ImportError:
    pass

from core.config import Colors, ConfigManager, USER_AGENTS


def run_github_dorking():
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- GitHub Code & Secret Dorking (Repository Scanner) ---{Colors.RESET}")
    target = input(f"{Colors.GREEN}[+] Target Domain or Org Keyword (e.g. example.com): {Colors.RESET}").strip()
    if not target:
        return

    print("  [1] Sensitive Configuration Files (filename:.env OR filename:config)")
    print("  [2] Leaked API Keys / Tokens (\"api_key\" OR \"secret_key\" OR \"access_token\")")
    print("  [3] Database Passwords & Credentials (\"password\" OR \"jdbc:\" OR \"mongodb://\")")
    print("  [4] Custom GitHub Code Search Query")
    opt = input(f"\n{Colors.GREEN}[+] Select Option (1-4): {Colors.RESET}").strip()

    if opt == "1":
        q = f'"{target}" filename:.env OR "{target}" filename:config.json OR "{target}" filename:wp-config.php'
    elif opt == "2":
        q = f'"{target}" "api_key" OR "{target}" "secret_key" OR "{target}" "access_token" OR "{target}" "Authorization: Bearer"'
    elif opt == "3":
        q = f'"{target}" "password" OR "{target}" "db_password" OR "{target}" "jdbc:" OR "{target}" "mongodb://"'
    elif opt == "4":
        custom = input(f"{Colors.GREEN}[+] Enter custom query: {Colors.RESET}").strip()
        q = f'"{target}" {custom}' if custom else f'"{target}"'
    else:
        q = f'"{target}" filename:.env'

    cfg = ConfigManager.load_config()
    gh_tok = cfg.get("github_api_token", "").strip()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": random.choice(USER_AGENTS)}
    if gh_tok:
        headers["Authorization"] = f"Bearer {gh_tok}"
    else:
        print(f"{Colors.YELLOW}[!] No GitHub API token configured in settings. Rate limits may be strict (10 req/min).{Colors.RESET}")

    url = f"https://api.github.com/search/code?q={urllib.parse.quote_plus(q)}&per_page=15"
    print(f"\n{Colors.YELLOW}[*] Scanning GitHub Repositories for: {q}...{Colors.RESET}")
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Found {len(items)} matching GitHub code references:{Colors.RESET}")
            for idx, item in enumerate(items, 1):
                repo = item.get("repository", {}).get("full_name", "Unknown Repo")
                path = item.get("path", "Unknown File")
                html_url = item.get("html_url", "")
                print(f"  {Colors.BOLD}{Colors.CYAN}[{idx}]{Colors.RESET} {Colors.MAGENTA}{repo}{Colors.RESET} -> {Colors.YELLOW}{path}{Colors.RESET}")
                print(f"       URL: {Colors.WHITE}{html_url}{Colors.RESET}")
        elif resp.status_code in (403, 429):
            print(f"{Colors.RED}[!] GitHub rate limit triggered. Configure a Personal Access Token in Option 11.{Colors.RESET}")
        else:
            print(f"{Colors.RED}[!] GitHub API returned HTTP {resp.status_code}: {resp.text[:100]}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}[!] GitHub dorking failed: {e}{Colors.RESET}")
