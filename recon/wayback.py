# -*- coding: utf-8 -*-
"""
Wayback Machine historical archive mining module (CDX Explorer).
"""

import random
import urllib.parse
from datetime import datetime

try:
    import requests
except ImportError:
    pass

from core.config import Colors, USER_AGENTS
from recon.subdomains import clean_domain


def run_wayback_recon():
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Wayback Machine Historical Archive Recon (CDX Explorer) ---{Colors.RESET}")
    domain = input(f"{Colors.GREEN}[+] Target Domain (e.g. example.com): {Colors.RESET}").strip()
    if not domain:
        return
    domain = clean_domain(domain)
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
