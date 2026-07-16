# -*- coding: utf-8 -*-
"""
Configuration manager, colors, banner printing, and HTTP headers for WAF evasion.
"""

import os
import sys
import time
import json
import random

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15'
]

def get_random_headers():
    ua = random.choice(USER_AGENTS)
    headers = {
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }
    if 'Chrome' in ua or 'Edg' in ua:
        headers['Sec-Ch-Ua'] = '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"'
        headers['Sec-Ch-Ua-Mobile'] = '?0'
        headers['Sec-Ch-Ua-Platform'] = '"Windows"' if 'Windows' in ua else '"macOS"'
    return headers


def print_banner():
    banner_lines = [
        "",
        "              ██████╗  ██████╗ ██████╗ ██╗  ██╗██╗   ██╗",
        "              ██╔══██╗██╔═══██╗██╔══██╗██║ ██╔╝╚██╗ ██╔╝",
        "              ██║  ██║██║   ██║██████╔╝█████╔╝  ╚████╔╝ ",
        "              ██║  ██║██║   ██║██╔══██╗██╔═██╗   ╚██╔╝  ",
        "              ██████╔╝╚██████╔╝██║  ██║██║  ██╗   ██║   ",
        "              ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ",
        ""
    ]
    
    for line in banner_lines:
        print(Colors.CYAN + Colors.BOLD + line + Colors.RESET)
        sys.stdout.flush()
        time.sleep(0.005)

    subtitle = "      [ Advanced Multi-Engine Dorking & Dynamic Syntax Adapter ]\n"
    author_info = "            Author: rielax | https://github.com/TheRielax\n"
    for char in subtitle:
        print(Colors.MAGENTA + char, end="")
        sys.stdout.flush()
        time.sleep(0.003)
    for char in author_info:
        print(Colors.YELLOW + char, end="")
        sys.stdout.flush()
        time.sleep(0.002)
    print(Colors.RESET)


class ConfigManager:
    """
    Manages API keys and default settings.
    """
    CONFIG_FILE = "config.json"
    DEFAULT_CONFIG = {
        "google_api_key": "",
        "google_cse_id": "",
        "brave_api_key": "",
        "github_api_token": "",
        "jitter_min": 2.0,
        "jitter_max": 4.5
    }

    @classmethod
    def load_config(cls):
        config = cls.DEFAULT_CONFIG.copy()
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config.update(data)
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Could not parse {cls.CONFIG_FILE}: {e}{Colors.RESET}")
        else:
            try:
                with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
            except Exception:
                pass
        config["google_api_key"] = os.environ.get("GOOGLE_API_KEY", config.get("google_api_key", ""))
        config["google_cse_id"] = os.environ.get("GOOGLE_CSE_ID", config.get("google_cse_id", ""))
        config["brave_api_key"] = os.environ.get("BRAVE_API_KEY", config.get("brave_api_key", ""))
        config["github_api_token"] = os.environ.get("GITHUB_API_TOKEN", config.get("github_api_token", ""))
        return config

    @classmethod
    def save_config(cls, config_data):
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            print(f"{Colors.GREEN}[+] Configuration saved to {cls.CONFIG_FILE}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Failed to save configuration: {e}{Colors.RESET}")

    @classmethod
    def configure_interactive(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Official API Configuration Settings ---{Colors.RESET}")
        cfg = cls.load_config()
        print("Leave blank to keep current value.\n")
        
        g_api = input(f"{Colors.GREEN}[+] Google Custom Search API Key [{cfg['google_api_key'][:8]}...]: {Colors.RESET}").strip()
        if g_api:
            cfg["google_api_key"] = g_api
            
        g_cse = input(f"{Colors.GREEN}[+] Google Custom Search CSE ID [{cfg['google_cse_id']}]: {Colors.RESET}").strip()
        if g_cse:
            cfg["google_cse_id"] = g_cse
            
        b_api = input(f"{Colors.GREEN}[+] Brave Search API Key [{cfg['brave_api_key'][:8]}...]: {Colors.RESET}").strip()
        if b_api:
            cfg["brave_api_key"] = b_api

        gh_tok = input(f"{Colors.GREEN}[+] GitHub Personal Access Token [{cfg['github_api_token'][:8]}...]: {Colors.RESET}").strip()
        if gh_tok:
            cfg["github_api_token"] = gh_tok

        cls.save_config(cfg)
