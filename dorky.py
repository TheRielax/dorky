#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
 DORKY: Advanced Multi-Engine Dorking & Dynamic Syntax Adapter
 Author: rielax (https://github.com/TheRielax)
=============================================================================
 This tool dynamically builds, adapts, and executes advanced search engine
 dorks across multiple search engines (DuckDuckGo, Bing, Google, Brave, Yandex).
 Every search engine has distinct dorking operators; DORKY automatically
 translates queries into the exact syntax supported by each engine.
=============================================================================
"""

import sys
import os
import time
import json
import csv
import random
import re
import urllib.parse
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("\n[!] Error: 'requests' or 'beautifulsoup4' is not installed!")
    print("[!] Install with: pip install requests beautifulsoup4\n")
    sys.exit(1)

# Optional third-party search libraries (suppress IDE unresolved import warnings)
try:
    from ddgs import DDGS  # type: ignore
except ImportError:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        DDGS = None

try:
    from googlesearch import search as google_search  # type: ignore
except ImportError:
    google_search = None

try:
    import phonenumbers  # type: ignore
    from phonenumbers import geocoder, carrier, timezone  # type: ignore
except ImportError:
    phonenumbers = None


if sys.version_info.major < 3:
    print("\n[x] Error: DORKY requires Python 3.x!\n")
    sys.exit(1)


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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0'
]


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


class HistoryManager:
    """
    Persistent session & search history tracking.
    Inspired by Deep-Dork history management.
    """
    HISTORY_FILE = "history.json"

    @classmethod
    def log_search(cls, query, engine_results, target_domain=""):
        history = cls.load_history()
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "target_domain": target_domain,
            "engines": {}
        }
        for eng, data in engine_results.items():
            entry["engines"][eng] = {
                "adapted_query": data.get("adapted_query", ""),
                "results_count": len(data.get("urls", []))
            }
        history.insert(0, entry)
        history = history[:100]
        try:
            with open(cls.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass

    @classmethod
    def load_history(cls):
        if os.path.exists(cls.HISTORY_FILE):
            try:
                with open(cls.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        else:
            try:
                with open(cls.HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4)
            except Exception:
                pass
        return []

    @classmethod
    def view_and_rerun(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Search History Sessions ---{Colors.RESET}")
        history = cls.load_history()
        if not history:
            print(f"{Colors.YELLOW}[!] No search history found.{Colors.RESET}")
            return None

        for idx, entry in enumerate(history[:15], 1):
            ts = entry.get("timestamp", "")
            q = entry.get("query", "")
            eng_summary = ", ".join([f"{k} ({v['results_count']})" for k, v in entry.get("engines", {}).items()])
            print(f"  {Colors.CYAN}[{idx}]{Colors.RESET} {ts} | {Colors.YELLOW}{q}{Colors.RESET} | Engines: {eng_summary}")

        print("  [0] Return to main menu")
        choice = input(f"\n{Colors.GREEN}[+] Select history entry to re-run (0-{min(len(history), 15)}): {Colors.RESET}").strip()
        try:
            val = int(choice)
            if 1 <= val <= len(history):
                return history[val - 1].get("query")
        except ValueError:
            pass
        return None


class DorkAdapter:
    """
    Translates canonical/Google-style dork queries into engine-specific syntax.
    """
    @staticmethod
    def adapt(query, engine):
        engine = engine.lower()
        adapted = query

        if engine in ["duckduckgo", "bing"]:
            # Bing/DDG support inbody: instead of intext: / allintext:
            adapted = re.sub(r'\ballintext:', 'inbody:', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\bintext:', 'inbody:', adapted, flags=re.IGNORECASE)
            # Replace allintitle: / allinurl: with intitle: / inurl:
            adapted = re.sub(r'\ballintitle:', 'intitle:', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\ballinurl:', 'inurl:', adapted, flags=re.IGNORECASE)

        elif engine == "yandex":
            # Yandex uses mime: instead of filetype: / ext:
            adapted = re.sub(r'\b(?:filetype|ext):([a-zA-Z0-9_-]+)', r'mime:\1', adapted, flags=re.IGNORECASE)
            # Yandex uses title: instead of intitle: / allintitle:
            adapted = re.sub(r'\b(?:intitle|allintitle):', 'title:', adapted, flags=re.IGNORECASE)
            # Yandex uses url: instead of inurl: / allinurl:
            adapted = re.sub(r'\b(?:inurl|allinurl):', 'url:', adapted, flags=re.IGNORECASE)
            # Yandex doesn't support intext: operator directly; convert to plain string search
            adapted = re.sub(r'\b(?:intext|allintext):("[^"]+"|\S+)', r'\1', adapted, flags=re.IGNORECASE)

        elif engine == "brave":
            # Brave Search supports site:, filetype:, intitle:, inurl:.
            # Convert unsupported intext:/allintext: to keywords
            adapted = re.sub(r'\b(?:intext|allintext|inbody):("[^"]+"|\S+)', r'\1', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\b(?:allintitle):', 'intitle:', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\b(?:allinurl):', 'inurl:', adapted, flags=re.IGNORECASE)

        # Google supports canonical dorks naturally
        return adapted


class SearchEngines:
    """
    Executes search queries against multiple engines using APIs or web scraping fallbacks.
    """
    @staticmethod
    def is_valid_url(url):
        # Validate URL string and filter out search engine tracking/redirect links
        if not url or not isinstance(url, str):
            return False
        url_str = url.strip()
        if not (url_str.startswith("http://") or url_str.startswith("https://")):
            return False
        invalid_sub = [
            "/clev?", "StartpageResultClick", "payload=",
            "google.com/url?", "bing.com/aclick", "yandex.ru/clck",
            "startpage.com/clev", "brave.com/", "duckduckgo.com/y.js"
        ]
        for sub in invalid_sub:
            if sub in url_str:
                return False
        return True

    @staticmethod
    def search_duckduckgo(query, max_results):
        results = []
        if DDGS is None:
            print(f"{Colors.RED}[!] DuckDuckGo error: 'ddgs' library not installed.{Colors.RESET}")
            return results
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                        results.append(r['href'])
        except Exception as e:
            print(f"{Colors.RED}[!] DuckDuckGo search failed: {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_bing(query, max_results):
        results = []
        if DDGS is None:
            print(f"{Colors.RED}[!] Bing error: 'ddgs' library not installed.{Colors.RESET}")
            return results
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, backend="bing", max_results=max_results):
                    if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                        results.append(r['href'])
        except Exception as e:
            print(f"{Colors.RED}[!] Bing search failed: {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_google(query, max_results):
        results = []
        cfg = ConfigManager.load_config()
        g_key = cfg.get("google_api_key", "").strip()
        g_cse = cfg.get("google_cse_id", "").strip()
        if g_key and g_cse:
            try:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://www.googleapis.com/customsearch/v1?q={encoded}&key={g_key}&cx={g_cse}&num={min(max_results, 10)}"
                headers = {'Accept-Encoding': 'gzip, deflate'}
                resp = requests.get(url, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        link = item.get("link")
                        if link and SearchEngines.is_valid_url(link) and link not in results:
                            results.append(link)
                    if results:
                        return results
                else:
                    print(f"{Colors.YELLOW}[!] Google Custom Search API returned HTTP {resp.status_code}. Falling back to scraping...{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Google API request failed: {e}. Falling back to scraping...{Colors.RESET}")

        if DDGS is not None:
            for b_end in ["google", "bing", "mojeek", "yandex", "yahoo", "duckduckgo", "startpage"]:
                try:
                    with DDGS() as ddgs:
                        for r in ddgs.text(query, backend=b_end, max_results=max_results):
                            if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                                results.append(r['href'])
                    if results:
                        return results
                except Exception:
                    continue

        if google_search is None:
            if not results:
                print(f"{Colors.RED}[!] Google error: 'googlesearch-python' library not installed.{Colors.RESET}")
            return results
        try:
            count = 0
            for url in google_search(query, num_results=max_results):
                if SearchEngines.is_valid_url(url) and url not in results:
                    results.append(url)
                    count += 1
                    if count >= max_results:
                        break
                    time.sleep(0.5)
        except Exception as e:
            if not results:
                print(f"{Colors.RED}[!] Google search failed (possibly rate-limited): {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_brave(query, max_results):
        results = []
        cfg = ConfigManager.load_config()
        b_key = cfg.get("brave_api_key", "").strip()
        if b_key:
            try:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={min(max_results, 20)}"
                headers = {"Accept": "application/json", "Accept-Encoding": "gzip, deflate", "X-Subscription-Token": b_key}
                resp = requests.get(url, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    web_res = data.get("web", {}).get("results", [])
                    for item in web_res:
                        u = item.get("url")
                        if u and SearchEngines.is_valid_url(u) and u not in results:
                            results.append(u)
                    if results:
                        return results
                else:
                    print(f"{Colors.YELLOW}[!] Brave API returned HTTP {resp.status_code}. Falling back to scraping...{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Brave API failed: {e}. Falling back to scraping...{Colors.RESET}")

        if DDGS is not None:
            for b_end in ["brave", "bing", "mojeek", "yandex", "yahoo", "duckduckgo", "startpage"]:
                try:
                    with DDGS() as ddgs:
                        for r in ddgs.text(query, backend=b_end, max_results=max_results):
                            if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                                results.append(r['href'])
                    if results:
                        return results
                except Exception:
                    continue

        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Encoding': 'gzip, deflate'
        }
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://search.brave.com/search?q={encoded_query}"
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if SearchEngines.is_valid_url(href) and 'brave.com' not in href and href not in results:
                        results.append(href)
                        if len(results) >= max_results:
                            break
            else:
                if not results:
                    print(f"{Colors.YELLOW}[!] Brave returned HTTP {response.status_code} (Rate-limited).{Colors.RESET}")
        except Exception as e:
            if not results:
                print(f"{Colors.RED}[!] Brave search failed: {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_yandex(query, max_results):
        results = []
        if DDGS is not None:
            for b_end in ["yandex", "bing", "mojeek", "yahoo", "duckduckgo", "startpage"]:
                try:
                    with DDGS() as ddgs:
                        for r in ddgs.text(query, backend=b_end, max_results=max_results):
                            if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                                results.append(r['href'])
                    if results:
                        return results
                except Exception:
                    continue

        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Encoding': 'gzip, deflate'
        }
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://yandex.com/search/?text={encoded_query}"
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_str = soup.title.string.lower() if soup.title and soup.title.string else ""
                if 'verification' in title_str or 'captcha' in title_str:
                    if not results:
                        print(f"{Colors.YELLOW}[!] Yandex CAPTCHA verification triggered.{Colors.RESET}")
                else:
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        if SearchEngines.is_valid_url(href) and 'yandex.' not in href and 'yastatic.net' not in href and href not in results:
                            results.append(href)
                            if len(results) >= max_results:
                                break
            else:
                if not results:
                    print(f"{Colors.YELLOW}[!] Yandex returned HTTP {response.status_code}.{Colors.RESET}")
        except Exception as e:
            if not results:
                print(f"{Colors.RED}[!] Yandex search failed: {e}{Colors.RESET}")
        return results


class DorkBuilder:
    """
    Interactive menu to construct customized dork strings.
    """
    @staticmethod
    def run():
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Interactive Dork Builder ---{Colors.RESET}")
        print("Leave blank any field you wish to skip.\n")

        site = input(f"{Colors.GREEN}[+] Target Domain / Site (e.g., example.com): {Colors.RESET}").strip()
        filetype = input(f"{Colors.GREEN}[+] File Extension (e.g., pdf, env, log, sql, txt): {Colors.RESET}").strip()
        intitle = input(f"{Colors.GREEN}[+] Keywords in Page Title (e.g., index of, admin login): {Colors.RESET}").strip()
        inurl = input(f"{Colors.GREEN}[+] Keywords in URL (e.g., wp-admin, config, backup): {Colors.RESET}").strip()
        intext = input(f"{Colors.GREEN}[+] Keywords in Page Body (e.g., password, secret_key): {Colors.RESET}").strip()
        exact = input(f"{Colors.GREEN}[+] Exact Phrase Match (e.g., \"confidential data\"): {Colors.RESET}").strip()
        exclude = input(f"{Colors.GREEN}[+] Exclude Words (e.g., public sample demo): {Colors.RESET}").strip()

        dork_parts = []
        if site:
            dork_parts.append(f"site:{site}")
        if filetype:
            # Handle multiple extensions separated by comma or space
            exts = [e.strip().lstrip('.') for e in re.split(r'[, ]+', filetype) if e.strip()]
            if len(exts) == 1:
                dork_parts.append(f"filetype:{exts[0]}")
            elif len(exts) > 1:
                ext_query = " OR ".join([f"filetype:{e}" for e in exts])
                dork_parts.append(f"({ext_query})")
        if intitle:
            if " " in intitle and not intitle.startswith('"'):
                dork_parts.append(f'intitle:"{intitle}"')
            else:
                dork_parts.append(f"intitle:{intitle}")
        if inurl:
            dork_parts.append(f"inurl:{inurl}")
        if intext:
            if " " in intext and not intext.startswith('"'):
                dork_parts.append(f'intext:"{intext}"')
            else:
                dork_parts.append(f"intext:{intext}")
        if exact:
            if not exact.startswith('"'):
                exact = f'"{exact}"'
            dork_parts.append(exact)
        if exclude:
            words = exclude.split()
            for w in words:
                dork_parts.append(f"-{w.lstrip('-')}")

        generated_query = " ".join(dork_parts)
        if not generated_query:
            print(f"{Colors.YELLOW}[!] No fields provided. Using generic test query.{Colors.RESET}")
            generated_query = "intitle:\"index of\""

        print(f"\n{Colors.BOLD}{Colors.CYAN}[*] Generated Canonical Query:{Colors.RESET} {Colors.YELLOW}{generated_query}{Colors.RESET}\n")
        return generated_query


class TemplateManager:
    """
    Pre-built OSINT & Vulnerability reconnaissance templates.
    """
    TEMPLATES = {
        "1": ("Exposed Configuration Files (.env, .ini, .conf, .yaml)", 'filetype:env OR filetype:ini OR filetype:conf OR filetype:yaml "password"'),
        "2": ("Exposed Database Dumps (.sql, .db, .sqlite)", 'filetype:sql OR filetype:db OR filetype:sqlite "insert into" OR "phpmyadmin"'),
        "3": ("Sensitive Log Files (.log)", 'filetype:log "error" OR "warning" OR "password" OR "exception"'),
        "4": ("Directory Listing / Open Index", 'intitle:"index of /" OR intitle:"parent directory"'),
        "5": ("Admin Login Panels & Dashboards", 'intitle:"admin login" OR inurl:admin login OR intitle:"dashboard login"'),
        "6": ("API Keys, Tokens & Secrets", '"api_key" OR "access_token" OR "secret_key" filetype:txt OR filetype:env')
    }

    @classmethod
    def select_template(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Reconnaissance Dork Templates ---{Colors.RESET}")
        for key, (desc, _) in cls.TEMPLATES.items():
            print(f"  [{key}] {desc}")
        print("  [0] Return to main menu")

        choice = input(f"\n{Colors.GREEN}[+] Select Template (0-6): {Colors.RESET}").strip()
        if choice in cls.TEMPLATES:
            desc, query = cls.TEMPLATES[choice]
            site = input(f"{Colors.GREEN}[+] Optionally limit to a target domain (leave empty for global): {Colors.RESET}").strip()
            if site:
                query = f"site:{site} {query}"
            print(f"\n{Colors.BOLD}{Colors.CYAN}[*] Selected Query ({desc}):{Colors.RESET} {Colors.YELLOW}{query}{Colors.RESET}\n")
            return query
        return None


class BatchManager:
    """
    Automated execution of multiple dorks from a file against selected engines.
    Inspired by Google-Dorking-Automation and Deep-Dork batch execution.
    """
    @classmethod
    def run_batch(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Batch Dork Execution from File ---{Colors.RESET}")
        filepath = input(f"{Colors.GREEN}[+] Enter path to dork wordlist [.txt] (default: dorks_sample.txt): {Colors.RESET}").strip() or "dorks_sample.txt"
        if not os.path.exists(filepath):
            print(f"{Colors.RED}[!] File not found: {filepath}{Colors.RESET}")
            return

        queries = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        queries.append(line)
        except Exception as e:
            print(f"{Colors.RED}[!] Error reading {filepath}: {e}{Colors.RESET}")
            return

        if not queries:
            print(f"{Colors.YELLOW}[!] No valid dorks found in {filepath}.{Colors.RESET}")
            return

        print(f"{Colors.GREEN}[+] Loaded {len(queries)} dorks from {filepath}.{Colors.RESET}")
        target_domain = input(f"{Colors.GREEN}[+] Optionally limit to a target domain (e.g. target.com): {Colors.RESET}").strip()

        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Select Target Search Engines for Batch ---{Colors.RESET}")
        print("  [1] DuckDuckGo")
        print("  [2] Bing")
        print("  [3] Google")
        print("  [4] Brave")
        print("  [5] Yandex")
        print("  [6] ALL ENGINES")
        engine_choice = input(f"\n{Colors.GREEN}[+] Select Option (1-6): {Colors.RESET}").strip()

        engines_to_run = []
        if engine_choice == "1":
            engines_to_run = [("DuckDuckGo", SearchEngines.search_duckduckgo)]
        elif engine_choice == "2":
            engines_to_run = [("Bing", SearchEngines.search_bing)]
        elif engine_choice == "3":
            engines_to_run = [("Google", SearchEngines.search_google)]
        elif engine_choice == "4":
            engines_to_run = [("Brave Search", SearchEngines.search_brave)]
        elif engine_choice == "5":
            engines_to_run = [("Yandex", SearchEngines.search_yandex)]
        elif engine_choice == "6":
            engines_to_run = [
                ("DuckDuckGo", SearchEngines.search_duckduckgo),
                ("Bing", SearchEngines.search_bing),
                ("Google", SearchEngines.search_google),
                ("Brave Search", SearchEngines.search_brave),
                ("Yandex", SearchEngines.search_yandex)
            ]
        else:
            engines_to_run = [("DuckDuckGo", SearchEngines.search_duckduckgo)]

        try:
            max_res = int(input(f"{Colors.GREEN}[+] Results per query per engine (default: 5): {Colors.RESET}").strip() or "5")
        except ValueError:
            max_res = 5

        cfg = ConfigManager.load_config()
        j_min = float(cfg.get("jitter_min", 2.0))
        j_max = float(cfg.get("jitter_max", 4.5))

        print(f"\n{Colors.BOLD}{Colors.WHITE} EXECUTING BATCH DORK SESSION ({len(queries)} queries across {len(engines_to_run)} engines){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Random jitter between requests: {j_min}s - {j_max}s{Colors.RESET}")

        batch_results = {}
        total_found = 0

        for q_idx, q in enumerate(queries, 1):
            full_query = f"site:{target_domain} {q}" if target_domain else q
            print(f"\n{Colors.BOLD}{Colors.CYAN}[{q_idx}/{len(queries)}] Processing Query:{Colors.RESET} {Colors.WHITE}{full_query}{Colors.RESET}")

            query_data = {}
            for eng_name, eng_func in engines_to_run:
                adapted = DorkAdapter.adapt(full_query, eng_name)
                urls = eng_func(adapted, max_res)
                query_data[eng_name] = {"adapted_query": adapted, "urls": urls}
                if urls:
                    print(f"{Colors.GREEN}    -> {eng_name}: Found {len(urls)} URLs{Colors.RESET}")
                    total_found += len(urls)
                else:
                    print(f"{Colors.RED}    -> {eng_name}: 0 results{Colors.RESET}")
                time.sleep(random.uniform(j_min, j_max))

            HistoryManager.log_search(full_query, query_data, target_domain)
            batch_results[f"Query #{q_idx}: {full_query}"] = query_data

        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Batch execution complete. Total URLs found: {total_found}{Colors.RESET}")
        save_opt = input(f"{Colors.GREEN}[+] Save batch results to file? (y/N): {Colors.RESET}").strip().lower()
        if save_opt.startswith('y'):
            base_fn = input(f"{Colors.GREEN}[+] Enter base filename [batch_results]: {Colors.RESET}").strip() or "batch_results"
            fmt_input = input(f"{Colors.GREEN}[+] Select format [txt/json/csv] (default: txt): {Colors.RESET}").strip().lower()
            output_fmt = fmt_input if fmt_input in ["json", "csv"] else "txt"
            save_results(batch_results, base_fn, output_fmt)


class ReconManager:
    """
    Modern OSINT & passive reconnaissance suite.
    Provides passive subdomain discovery, Wayback archive mining, GitHub secret dorking, and tech stack detection.
    """
    @staticmethod
    def clean_domain(domain):
        d = domain.strip().lower()
        d = re.sub(r'^https?://', '', d)
        return d.rstrip('/')

    @classmethod
    def subdomain_recon(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Passive Subdomain Enumeration (crt.sh Certificate Logs) ---{Colors.RESET}")
        domain = input(f"{Colors.GREEN}[+] Target Domain (e.g. example.com): {Colors.RESET}").strip()
        if not domain:
            return
        domain = cls.clean_domain(domain)
        subdomains = set()
        headers = {'User-Agent': random.choice(USER_AGENTS)}

        # 1. crt.sh Certificate Transparency
        print(f"{Colors.YELLOW}[*] Querying Certificate Transparency logs (crt.sh) for *.{domain}...{Colors.RESET}")
        try:
            url_crt = f"https://crt.sh/?q=%.{domain}&output=json"
            resp = requests.get(url_crt, timeout=20, headers=headers)
            if resp.status_code == 200:
                for item in resp.json():
                    name_val = item.get("name_value", "")
                    for line in name_val.split('\n'):
                        line = line.strip().lower().lstrip('*.')
                        if line.endswith(domain) and line != domain and not ' ' in line:
                            subdomains.add(line)
            else:
                print(f"{Colors.RED}[!] crt.sh returned HTTP {resp.status_code}. Pivoting to backup sources...{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}[!] crt.sh query timed out or failed ({e}). Pivoting to secondary OSINT sources...{Colors.RESET}")

        # 2. HackerTarget HostSearch API
        print(f"{Colors.YELLOW}[*] Querying HackerTarget Passive DNS for *.{domain}...{Colors.RESET}")
        try:
            url_ht = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            resp_ht = requests.get(url_ht, timeout=15, headers=headers)
            if resp_ht.status_code == 200 and "error" not in resp_ht.text.lower():
                for line in resp_ht.text.splitlines():
                    parts = line.split(',')
                    if parts:
                        sub = parts[0].strip().lower().lstrip('*.')
                        if sub.endswith(domain) and sub != domain and not ' ' in sub:
                            subdomains.add(sub)
        except Exception:
            pass

        # 3. UrlScan.io Search API
        print(f"{Colors.YELLOW}[*] Querying UrlScan.io Index for *.{domain}...{Colors.RESET}")
        try:
            url_us = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
            resp_us = requests.get(url_us, timeout=15, headers=headers)
            if resp_us.status_code == 200:
                for item in resp_us.json().get("results", []):
                    sub = item.get("page", {}).get("domain", "").strip().lower().lstrip('*.')
                    if sub.endswith(domain) and sub != domain and not ' ' in sub:
                        subdomains.add(sub)
        except Exception:
            pass

        subs_sorted = sorted(list(subdomains))
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Discovered {len(subs_sorted)} unique subdomains for {domain}:{Colors.RESET}")
        for idx, sub in enumerate(subs_sorted[:100], 1):
            print(f"  {Colors.CYAN}[{idx:>3}]{Colors.RESET} {Colors.WHITE}{sub}{Colors.RESET}")

        if len(subs_sorted) > 100:
            print(f"{Colors.YELLOW}... and {len(subs_sorted) - 100} more.{Colors.RESET}")

        if subs_sorted:
            opt = input(f"\n{Colors.GREEN}[+] Save subdomains to file or run DORKY search against one? [save/search/Enter=Back]: {Colors.RESET}").strip().lower()
            if opt.startswith('s') and 'sav' in opt:
                filename = f"subdomains_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(subs_sorted))
                print(f"{Colors.GREEN}[+] Saved to {filename}{Colors.RESET}")
            elif opt.startswith('s') and 'sear' in opt:
                choice = input(f"{Colors.GREEN}[+] Enter index number of subdomain to dork (1-{min(len(subs_sorted), 100)}): {Colors.RESET}").strip()
                try:
                    val = int(choice)
                    if 1 <= val <= len(subs_sorted):
                        run_search_session(f"site:{subs_sorted[val-1]}")
                except ValueError:
                    pass

    @classmethod
    def wayback_recon(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Wayback Machine Historical Archive Recon (CDX Explorer) ---{Colors.RESET}")
        domain = input(f"{Colors.GREEN}[+] Target Domain (e.g. example.com): {Colors.RESET}").strip()
        if not domain:
            return
        domain = cls.clean_domain(domain)
        ext_input = input(f"{Colors.GREEN}[+] Sensitive file extensions comma-separated [default: env,ini,conf,sql,log,bak,zip,git]: {Colors.RESET}").strip()
        exts = [e.strip().lstrip('.') for e in (ext_input.split(',') if ext_input else ['env', 'ini', 'conf', 'sql', 'log', 'bak', 'zip', 'git']) if e.strip()]

        print(f"{Colors.YELLOW}[*] Mining Internet Archive historical index for *.{domain} matching extensions: {', '.join(exts)}...{Colors.RESET}")
        url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original,timestamp&collapse=urlkey&limit=500"
        found_endpoints = []
        try:
            resp = requests.get(url, timeout=20, headers={'User-Agent': random.choice(USER_AGENTS)})
            if resp.status_code == 200:
                rows = resp.json()
                if len(rows) > 1:
                    for row in rows[1:]:
                        orig_url, ts = row[0], row[1]
                        parsed_path = urllib.parse.urlparse(orig_url).path.lower()
                        if any(parsed_path.endswith(f".{x}") for x in exts):
                            fmt_ts = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts
                            found_endpoints.append((orig_url, fmt_ts))
            else:
                print(f"{Colors.RED}[!] CDX API returned HTTP {resp.status_code}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Wayback recon failed: {e}{Colors.RESET}")

        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Found {len(found_endpoints)} archived historical endpoints:{Colors.RESET}")
        for idx, (u, t) in enumerate(found_endpoints[:50], 1):
            print(f"  {Colors.CYAN}[{t}]{Colors.RESET} {Colors.WHITE}{u}{Colors.RESET}")

        if len(found_endpoints) > 50:
            print(f"{Colors.YELLOW}... and {len(found_endpoints) - 50} more.{Colors.RESET}")

        if found_endpoints:
            opt = input(f"\n{Colors.GREEN}[+] Save archived URLs to file? (y/N): {Colors.RESET}").strip().lower()
            if opt.startswith('y'):
                filename = f"wayback_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    for u, t in found_endpoints:
                        f.write(f"[{t}] {u}\n")
                print(f"{Colors.GREEN}[+] Saved to {filename}{Colors.RESET}")

    @classmethod
    def github_dorking(cls):
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

    @classmethod
    def technology_detector(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Web Technology & CMS Fingerprinter (Stack Detector) ---{Colors.RESET}")
        target_url = input(f"{Colors.GREEN}[+] Enter Target URL (e.g. https://example.com): {Colors.RESET}").strip()
        if not target_url:
            return
        if not target_url.startswith('http'):
            target_url = "https://" + target_url

        print(f"{Colors.YELLOW}[*] Sending fingerprint probe to {target_url}...{Colors.RESET}")
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        try:
            resp = requests.get(target_url, headers=headers, timeout=12, verify=True)
        except requests.exceptions.SSLError:
            try:
                resp = requests.get(target_url, headers=headers, timeout=12, verify=False)
            except Exception as e:
                print(f"{Colors.RED}[!] Could not connect to {target_url}: {e}{Colors.RESET}")
                return
        except Exception as e:
            print(f"{Colors.RED}[!] Could not connect to {target_url}: {e}{Colors.RESET}")
            return

        techs = []
        h = resp.headers
        if 'Server' in h:
            techs.append(f"Server: {h['Server']}")
        if 'X-Powered-By' in h:
            techs.append(f"Powered-By: {h['X-Powered-By']}")
        if 'CF-Ray' in h or 'server' in h and 'cloudflare' in h.get('server', '').lower():
            techs.append("WAF/CDN: Cloudflare")
        if 'X-Generator' in h:
            techs.append(f"Generator: {h['X-Generator']}")

        # Cookie analysis
        cookies_str = " ".join(resp.cookies.keys()).lower()
        if 'phpsessid' in cookies_str:
            techs.append("Backend: PHP")
        elif 'jsessionid' in cookies_str:
            techs.append("Backend: Java/JSP")
        elif 'aspsessionid' in cookies_str or 'asp.net' in str(h).lower():
            techs.append("Backend: ASP.NET")
        elif 'laravel' in cookies_str:
            techs.append("Framework: Laravel (PHP)")
        elif 'csrftoken' in cookies_str or 'sessionid' in cookies_str:
            techs.append("Framework potential: Django/Python")

        # HTML DOM analysis
        soup = BeautifulSoup(resp.text, 'html.parser')
        meta_gen = soup.find('meta', attrs={'name': re.compile(r'generator', re.I)})
        if meta_gen and meta_gen.get('content'):
            techs.append(f"CMS/Generator: {meta_gen['content'].strip()}")

        html_text = resp.text.lower()
        if 'wp-content' in html_text or 'wp-includes' in html_text:
            techs.append("CMS: WordPress")
        if 'joomla' in html_text:
            techs.append("CMS: Joomla")
        if 'drupal' in html_text:
            techs.append("CMS: Drupal")
        if '/_next/static' in html_text:
            techs.append("Frontend Framework: Next.js (React)")
        elif 'data-reactroot' in html_text or 'react' in html_text:
            techs.append("Frontend Library: React")
        if 'ng-app' in html_text or 'ng-controller' in html_text:
            techs.append("Frontend Framework: Angular")
        if 'vue' in html_text or 'data-v-' in html_text:
            techs.append("Frontend Framework: Vue.js")
        if 'bootstrap' in html_text:
            techs.append("UI Library: Bootstrap")
        if 'tailwind' in html_text:
            techs.append("UI Library: Tailwind CSS")

        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Fingerprint Summary for {target_url} (HTTP {resp.status_code}):{Colors.RESET}")
        if techs:
            for t in sorted(list(set(techs))):
                parts = t.split(':', 1)
                if len(parts) == 2:
                    print(f"  {Colors.CYAN}{parts[0]:<20}:{Colors.RESET} {Colors.WHITE}{parts[1].strip()}{Colors.RESET}")
                else:
                    print(f"  {Colors.YELLOW}[•]{Colors.RESET} {Colors.WHITE}{t}{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}[!] No specific CMS or stack signatures detected in headers/html.{Colors.RESET}")

        print(f"\n{Colors.CYAN}[💡 Recommended Action]{Colors.RESET} Based on detected tech, you can use Option 1 or Option 2 to launch targeted dorks against {target_url}.\n")

    @classmethod
    def phone_osint(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Phone Number OSINT & Footprinting Suite ---{Colors.RESET}")
        number_str = input(f"{Colors.GREEN}[+] Target Phone Number (e.g. +39 340 1234567 or 02 1234567): {Colors.RESET}").strip()
        if not number_str:
            return None

        region_code = None
        if not number_str.startswith('+'):
            region_input = input(f"{Colors.GREEN}[+] Default Country Code for national format (e.g. IT, US, FR - press Enter for IT): {Colors.RESET}").strip().upper()
            region_code = region_input if region_input else "IT"

        print(f"\n{Colors.YELLOW}[*] Executing phone intelligence analysis...{Colors.RESET}")

        e164 = number_str
        national = number_str
        intl = number_str
        location = "Unknown"
        carrier_name = "Unknown"
        line_type = "Unknown / General"
        timezones = []
        is_valid = False

        if phonenumbers is not None:
            try:
                parsed = phonenumbers.parse(number_str, region_code)
                is_valid = phonenumbers.is_valid_number(parsed)
                e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
                intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                
                loc_desc = geocoder.description_for_number(parsed, "en")
                if loc_desc:
                    location = loc_desc
                c_desc = carrier.name_for_number(parsed, "en")
                if c_desc:
                    carrier_name = c_desc
                tz_list = timezone.time_zones_for_number(parsed)
                if tz_list and tz_list != ('Etc/Unknown',):
                    timezones = list(tz_list)
                
                num_type = phonenumbers.number_type(parsed)
                type_map = {
                    0: "Fixed Line", 1: "Mobile", 2: "Fixed Line OR Mobile",
                    3: "Toll Free", 4: "Premium Rate", 5: "Shared Cost",
                    6: "VoIP", 7: "Personal Number", 8: "Pager",
                    9: "UAN", 10: "Voicemail"
                }
                line_type = type_map.get(num_type, "Unknown")
            except Exception as e:
                pass

        clean_digits = re.sub(r'\D', '', number_str)
        if not e164.startswith('+'):
            if region_code == "IT" and not clean_digits.startswith('39'):
                e164 = "+39" + clean_digits
                clean_digits = "39" + clean_digits
            elif clean_digits:
                e164 = "+" + clean_digits
        else:
            clean_digits = re.sub(r'\D', '', e164)

        if national == number_str and len(clean_digits) > 4:
            national = clean_digits[2:] if clean_digits.startswith('39') else clean_digits
        if intl == number_str and e164.startswith('+'):
            intl = e164

        # Built-in Deep Prefix & Carrier Intelligence Engine (Offline / Zero External Cost)
        cc_map = {
            "39": "Italy", "1": "USA / Canada (NANP)", "44": "United Kingdom", "33": "France",
            "49": "Germany", "34": "Spain", "41": "Switzerland", "43": "Austria", "31": "Netherlands",
            "32": "Belgium", "351": "Portugal", "30": "Greece", "46": "Sweden", "47": "Norway",
            "45": "Denmark", "358": "Finland", "48": "Poland", "420": "Czech Republic",
            "36": "Hungary", "40": "Romania", "380": "Ukraine", "7": "Russia / Kazakhstan",
            "86": "China", "81": "Japan", "82": "South Korea", "91": "India", "61": "Australia",
            "55": "Brazil", "52": "Mexico", "54": "Argentina", "27": "South Africa", "971": "UAE"
        }

        it_cities = {
            "06": "Roma (Lazio)", "02": "Milano (Lombardia)", "011": "Torino (Piemonte)",
            "081": "Napoli (Campania)", "055": "Firenze (Toscana)", "051": "Bologna (Emilia-Romagna)",
            "010": "Genova (Liguria)", "091": "Palermo (Sicilia)", "041": "Venezia (Veneto)",
            "080": "Bari (Puglia)", "095": "Catania (Sicilia)", "045": "Verona (Veneto)",
            "049": "Padova (Veneto)", "040": "Trieste (Friuli-Venezia Giulia)", "030": "Brescia (Lombardia)",
            "035": "Bergamo (Lombardia)", "0521": "Parma (Emilia-Romagna)", "059": "Modena (Emilia-Romagna)",
            "071": "Ancona (Marche)", "050": "Pisa (Toscana)", "075": "Perugia (Umbria)",
            "070": "Cagliari (Sardegna)", "090": "Messina (Sicilia)", "089": "Salerno (Campania)",
            "0541": "Rimini (Emilia-Romagna)", "0187": "La Spezia (Liguria)", "031": "Como (Lombardia)",
            "039": "Monza (Lombardia)", "0331": "Busto Arsizio / Varese (Lombardia)", "0862": "L'Aquila (Abruzzo)"
        }

        it_mobiles = {
            ("320", "327", "328", "329", "380", "388", "389", "390", "391", "392", "393"): "Wind Tre",
            ("330", "331", "333", "334", "335", "336", "337", "338", "339", "360", "366", "368"): "TIM (Telecom Italia Mobile)",
            ("340", "342", "345", "346", "347", "348", "349"): "Vodafone Italia",
            ("351", "352"): "Iliad Italia",
            ("370",): "TIM / MVNO (CoopVoce/Tiscali)",
            ("371",): "PosteMobile / Very Mobile",
            ("377",): "PosteMobile",
            ("378",): "Kena Mobile (MVNO TIM)",
            ("379",): "Fastweb / Eolo Mobile",
            ("350",): "Kena Mobile / MVNO"
        }

        if clean_digits.startswith("39") and len(clean_digits) > 4:
            local_part = clean_digits[2:]
            if location in ("Unknown", "Italy", ""):
                location = "Italy"
                if local_part.startswith("0"):
                    line_type = "Fixed Line" if line_type in ("Unknown / General", "Unknown") else line_type
                    for pfx, city in sorted(it_cities.items(), key=lambda x: len(x[0]), reverse=True):
                        if local_part.startswith(pfx):
                            location = f"Italy, {city}"
                            break
            if carrier_name in ("Unknown", "") and local_part.startswith("3"):
                line_type = "Mobile" if line_type in ("Unknown / General", "Unknown") else line_type
                pfx3 = local_part[:3]
                for pfx_tuple, c_name in it_mobiles.items():
                    if pfx3 in pfx_tuple:
                        carrier_name = c_name
                        break
            if local_part.startswith("800"):
                line_type = "Toll Free (Numero Verde)"
                location = "Italy (National Toll Free)"
            elif local_part.startswith("899") or local_part.startswith("892"):
                line_type = "Premium Rate (Servizio a Sovrapprezzo)"
                location = "Italy (Special Rate)"
            if not timezones:
                timezones = ["Europe/Rome"]
            is_valid = True if len(local_part) in (9, 10, 11) else is_valid
        else:
            if location in ("Unknown", ""):
                for cc, c_name in sorted(cc_map.items(), key=lambda x: len(x[0]), reverse=True):
                    if clean_digits.startswith(cc):
                        location = c_name
                        break

        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Phone Intelligence Summary:{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Validity':<22}:{Colors.RESET} {Colors.GREEN if is_valid else Colors.YELLOW}{'Valid Number' if is_valid else 'Possible/Unverified Format'}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'E.164 Format':<22}:{Colors.RESET} {Colors.WHITE}{e164}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Intl Format':<22}:{Colors.RESET} {Colors.WHITE}{intl}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'National Format':<22}:{Colors.RESET} {Colors.WHITE}{national}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Location / Region':<22}:{Colors.RESET} {Colors.WHITE}{location}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Carrier Operator':<22}:{Colors.RESET} {Colors.WHITE}{carrier_name}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Line Type':<22}:{Colors.RESET} {Colors.WHITE}{line_type}{Colors.RESET}")
        if timezones:
            print(f"  {Colors.CYAN}{'Timezone(s)':<22}:{Colors.RESET} {Colors.WHITE}{', '.join(timezones)}{Colors.RESET}")
        if "Mobile" in line_type or clean_digits.startswith("393"):
            print(f"  {Colors.CYAN}{'MNP Portability Note':<22}:{Colors.RESET} {Colors.YELLOW}Carrier indicates original ministerial block allocation (subject to MNP portability){Colors.RESET}")

        clean_num = re.sub(r'\D', '', e164)
        dorks = {
            "General Web Footprint": f'"{e164}" OR "{intl}" OR "{national}"',
            "Messaging & Social": f'("{e164}" OR "{clean_num}") (site:t.me OR site:wa.me OR site:facebook.com OR site:linkedin.com)',
            "Reputation & Spam Directories": f'("{e164}" OR "{clean_num}") (truecaller OR tellows OR sync.me OR "who called" OR spam OR truffa)',
            "Document & Paste Leak Search": f'("{e164}" OR "{clean_num}") (filetype:pdf OR filetype:txt OR site:pastebin.com)'
        }

        print(f"\n{Colors.CYAN}{Colors.BOLD}[+] Generated Phone Footprint Dorks:{Colors.RESET}")
        dork_list = list(dorks.items())
        for idx, (title, q) in enumerate(dork_list, 1):
            print(f"  {Colors.YELLOW}[{idx}] {title}:{Colors.RESET}")
            print(f"      {Colors.WHITE}{q}{Colors.RESET}")

        print(f"\n{Colors.GREEN}[+] Select a footprint query to launch multi-engine scan immediately (1-{len(dork_list)}, or Enter to return): {Colors.RESET}", end="")
        scan_choice = input().strip()
        if scan_choice.isdigit() and 1 <= int(scan_choice) <= len(dork_list):
            return dork_list[int(scan_choice)-1][1]
        return None



def show_syntax_guide():
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("                 SEARCH ENGINE DORK SYNTAX ADAPTATION GUIDE                  ")
    print("=============================================================================" + Colors.RESET)
    guide = [
        ("Google", "site:, filetype:/ext:, intitle:, allintitle:, inurl:, allinurl:, intext:, allintext:, \"\", -, OR"),
        ("DuckDuckGo / Bing", "site:, filetype:/ext:, intitle:, inurl:, inbody: (replaces intext:), \"\", -, OR"),
        ("Yandex", "site:, mime: (replaces filetype:), title: (replaces intitle:), url: (replaces inurl:), \"\", ~~/-"),
        ("Brave Search", "site:, filetype:, intitle:, inurl:, \"\", - (Unsupported operators converted to keywords)")
    ]
    for engine, syntax in guide:
        print(f"{Colors.BOLD}{Colors.MAGENTA}{engine:<18}{Colors.RESET} : {syntax}")
    print(f"{Colors.CYAN}============================================================================={Colors.RESET}\n")
    input(f"{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")


def save_results(results_data, base_filename, output_format):
    """Save collected search results to disk in TXT, JSON, or CSV format."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{base_filename}_{timestamp}.{output_format}"

    try:
        if output_format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=4)
        elif output_format == "csv":
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Engine", "Adapted Query", "Rank", "URL"])
                for engine, data in results_data.items():
                    query = data["adapted_query"]
                    for idx, url in enumerate(data["urls"], 1):
                        writer.writerow([engine, query, idx, url])
        else: # txt
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== DORKY SEARCH RESULTS ({timestamp}) ===\n\n")
                for engine, data in results_data.items():
                    f.write(f"--- Engine: {engine.upper()} ---\n")
                    f.write(f"Adapted Query: {data['adapted_query']}\n")
                    if data["urls"]:
                        for idx, url in enumerate(data["urls"], 1):
                            f.write(f"[{idx}] {url}\n")
                    else:
                        f.write("No results found.\n")
                    f.write("\n")
        print(f"{Colors.GREEN}{Colors.BOLD}[+] Results successfully saved to: {filename}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}[!] Failed to save results: {e}{Colors.RESET}")


def run_search_session(query):
    """Orchestrate search across selected engines, display results, and log history."""
    print(f"{Colors.CYAN}{Colors.BOLD}--- Select Target Search Engines ---{Colors.RESET}")
    print("  [1] DuckDuckGo (Privacy-focused, reliable)")
    print("  [2] Bing       (Fast, Microsoft index)")
    print("  [3] Google     (Comprehensive, may trigger captchas)")
    print("  [4] Brave      (Independent index)")
    print("  [5] Yandex     (Alternative index, distinct results)")
    print("  [6] ALL ENGINES (Simultaneous multi-engine query)")
    
    engine_choice = input(f"\n{Colors.GREEN}[+] Select Option (1-6): {Colors.RESET}").strip()
    
    engines_to_run = []
    if engine_choice == "1":
        engines_to_run = [("DuckDuckGo", SearchEngines.search_duckduckgo)]
    elif engine_choice == "2":
        engines_to_run = [("Bing", SearchEngines.search_bing)]
    elif engine_choice == "3":
        engines_to_run = [("Google", SearchEngines.search_google)]
    elif engine_choice == "4":
        engines_to_run = [("Brave Search", SearchEngines.search_brave)]
    elif engine_choice == "5":
        engines_to_run = [("Yandex", SearchEngines.search_yandex)]
    elif engine_choice == "6":
        engines_to_run = [
            ("DuckDuckGo", SearchEngines.search_duckduckgo),
            ("Bing", SearchEngines.search_bing),
            ("Google", SearchEngines.search_google),
            ("Brave Search", SearchEngines.search_brave),
            ("Yandex", SearchEngines.search_yandex)
        ]
    else:
        print(f"{Colors.YELLOW}[!] Invalid option. Defaulting to DuckDuckGo.{Colors.RESET}")
        engines_to_run = [("DuckDuckGo", SearchEngines.search_duckduckgo)]

    try:
        max_results = int(input(f"{Colors.GREEN}[+] Number of results per engine (e.g., 15): {Colors.RESET}").strip())
    except ValueError:
        print(f"{Colors.YELLOW}[!] Invalid number. Setting to 10.{Colors.RESET}")
        max_results = 10

    save_opt = input(f"{Colors.GREEN}[+] Save results to file? (y/N): {Colors.RESET}").strip().lower()
    base_filename = ""
    output_format = "txt"
    if save_opt.startswith('y'):
        base_filename = input(f"{Colors.GREEN}[+] Enter base filename (without extension): {Colors.RESET}").strip() or "dorky_results"
        fmt_input = input(f"{Colors.GREEN}[+] Select format [txt/json/csv] (default: txt): {Colors.RESET}").strip().lower()
        if fmt_input in ["json", "csv"]:
            output_format = fmt_input

    print(f"\n{Colors.BOLD}{Colors.CYAN}============================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE} EXECUTING DORKY SEARCH SESSION {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}============================================================================={Colors.RESET}")

    collected_data = {}

    for engine_name, search_func in engines_to_run:
        adapted_query = DorkAdapter.adapt(query, engine_name)
        print(f"\n{Colors.BOLD}{Colors.BLUE}[•] Target Engine:{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{engine_name}{Colors.RESET}")
        print(f"{Colors.MAGENTA}    Adapted Syntax: {Colors.YELLOW}{adapted_query}{Colors.RESET}")
        
        start_time = time.time()
        urls = search_func(adapted_query, max_results)
        elapsed = round(time.time() - start_time, 2)

        collected_data[engine_name] = {
            "adapted_query": adapted_query,
            "urls": urls
        }

        if urls:
            print(f"{Colors.GREEN}    Found {len(urls)} URLs in {elapsed}s:{Colors.RESET}")
            for idx, u in enumerate(urls, 1):
                print(f"     {Colors.BOLD}{idx:>2}.{Colors.RESET} {Colors.WHITE}{u}{Colors.RESET}")
                time.sleep(0.05)
        else:
            print(f"{Colors.RED}    No results found or request blocked ({elapsed}s).{Colors.RESET}")

        if len(engines_to_run) > 1:
            time.sleep(1.5)

    if collected_data:
        HistoryManager.log_search(query, collected_data)

    print(f"\n{Colors.BOLD}{Colors.CYAN}============================================================================={Colors.RESET}")
    if save_opt.startswith('y') and collected_data:
        save_results(collected_data, base_filename, output_format)


def main():
    """Main application loop handling CLI menu navigation."""
    while True:
        try:
            print_banner()
            print(f"{Colors.BOLD}{Colors.WHITE}Main Menu:{Colors.RESET}")
            print(f"  {Colors.BOLD}{Colors.MAGENTA}[-- Core Multi-Engine Dorking --]{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} Interactive Dork Builder {Colors.YELLOW}(Recommended){Colors.RESET}")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} Reconnaissance Vulnerability Templates")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} Enter Custom Raw Dork Query")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} Search Engine Syntax Adaptation Guide")
            print(f"  {Colors.CYAN}[5]{Colors.RESET} Batch Dork Execution from File")
            print(f"  {Colors.CYAN}[6]{Colors.RESET} Search History & Re-run")
            print(f"  {Colors.BOLD}{Colors.MAGENTA}[-- Target Recon & OSINT Suite --]{Colors.RESET}")
            print(f"  {Colors.CYAN}[7]{Colors.RESET} Passive Subdomain Enumeration (Certificate Logs)")
            print(f"  {Colors.CYAN}[8]{Colors.RESET} Wayback Machine Historical Archive Recon")
            print(f"  {Colors.CYAN}[9]{Colors.RESET} GitHub Code & Secret Dorking")
            print(f"  {Colors.CYAN}[10]{Colors.RESET} Web Technology & CMS Fingerprinter")
            print(f"  {Colors.CYAN}[11]{Colors.RESET} Phone Number OSINT & Footprinting")
            print(f"  {Colors.BOLD}{Colors.MAGENTA}[-- Settings & Exit --]{Colors.RESET}")
            print(f"  {Colors.CYAN}[12]{Colors.RESET} Official API Keys Configuration (Google, Brave, GitHub)")
            print(f"  {Colors.CYAN}[13]{Colors.RESET} Exit")

            choice = input(f"\n{Colors.GREEN}[+] Select Option (1-13): {Colors.RESET}").strip()

            if choice == "1":
                query = DorkBuilder.run()
                run_search_session(query)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "2":
                query = TemplateManager.select_template()
                if query:
                    run_search_session(query)
                    input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "3":
                query = input(f"\n{Colors.GREEN}[+] Enter Canonical/Google Dork Query: {Colors.RESET}").strip()
                if query:
                    run_search_session(query)
                    input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "4":
                show_syntax_guide()
            elif choice == "5":
                BatchManager.run_batch()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "6":
                query = HistoryManager.view_and_rerun()
                if query:
                    run_search_session(query)
                    input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "7":
                ReconManager.subdomain_recon()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "8":
                ReconManager.wayback_recon()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "9":
                ReconManager.github_dorking()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "10":
                ReconManager.technology_detector()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "11":
                query = ReconManager.phone_osint()
                if query:
                    run_search_session(query)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "12":
                ConfigManager.configure_interactive()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "13":
                print(f"\n{Colors.GREEN}{Colors.BOLD}[*] Thank you for using DORKY! Happy hunting!{Colors.RESET}\n")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}[!] Invalid selection. Please choose between 1 and 13.{Colors.RESET}\n")
                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.RED}{Colors.BOLD}[!] Session interrupted by user. Exiting DORKY...{Colors.RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
