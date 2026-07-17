# -*- coding: utf-8 -*-
"""
Passive Subdomain Enumeration module (crt.sh, HackerTarget, UrlScan).
"""

import re
import random
from datetime import datetime

try:
    import requests
except ImportError:
    pass

from core.config import Colors, USER_AGENTS


def clean_domain(domain):
    d = domain.strip().lower()
    d = re.sub(r'^https?://', '', d)
    return d.rstrip('/')


def enumerate_subdomains_passive(domain, quiet=False):
    """
    Programmatic passive subdomain enumeration across crt.sh, HackerTarget, and UrlScan.
    Returns sorted list of unique subdomains for `domain`.
    """
    domain = clean_domain(domain)
    subdomains = set()
    headers = {'User-Agent': random.choice(USER_AGENTS)}

    if not quiet:
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
            if not quiet:
                print(f"{Colors.RED}[!] crt.sh returned HTTP {resp.status_code}. Pivoting to backup sources...{Colors.RESET}")
    except Exception as e:
        if not quiet:
            print(f"{Colors.YELLOW}[!] crt.sh query timed out or failed ({e}). Pivoting to secondary OSINT sources...{Colors.RESET}")

    if not quiet:
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

    if not quiet:
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

    return sorted(list(subdomains))


def run_subdomain_recon(search_callback=None, domain=None):
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Passive Subdomain Enumeration (crt.sh Certificate Logs) ---{Colors.RESET}")
    if not domain:
        domain = input(f"{Colors.GREEN}[+] Target Domain (e.g. example.com): {Colors.RESET}").strip()
    if not domain:
        return
    domain = clean_domain(domain)
    
    subs_sorted = enumerate_subdomains_passive(domain, quiet=False)

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
        elif opt.startswith('s') and 'sear' in opt and search_callback:
            choice = input(f"{Colors.GREEN}[+] Enter index number of subdomain to dork (1-{min(len(subs_sorted), 100)}): {Colors.RESET}").strip()
            try:
                val = int(choice)
                if 1 <= val <= len(subs_sorted):
                    search_callback(f"site:{subs_sorted[val-1]}")
            except ValueError:
                pass
