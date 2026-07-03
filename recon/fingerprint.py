# -*- coding: utf-8 -*-
"""
Web technology and CMS fingerprinter (HTTP Headers & DOM Analysis).
"""

import re
import random

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    pass

from core.config import Colors, USER_AGENTS


def run_technology_detector():
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
