# -*- coding: utf-8 -*-
"""
Web technology and CMS fingerprinter (HTTP Headers, DOM & Site Tree Analysis).
"""

import re
import os
import json
import random
import urllib.parse
from datetime import datetime

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from bs4 import BeautifulSoup
except ImportError:
    pass

from core.config import Colors, USER_AGENTS


def fetch_site_tree_and_sitemap(target_url):
    """
    Explore robots.txt and sitemap.xml to discover site structure,
    disallowed paths, and build a top-level directory tree.
    """
    parsed = urllib.parse.urlparse(target_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    headers = {'User-Agent': random.choice(USER_AGENTS)}

    robots_disallow = []
    sitemap_candidates = []
    sitemap_urls = []
    tree_branches = {}

    # 1. Fetch robots.txt
    try:
        r_robots = requests.get(f"{base_url}/robots.txt", headers=headers, timeout=10, verify=False)
        if r_robots.status_code == 200:
            for line in r_robots.text.splitlines():
                line_clean = line.strip()
                if line_clean.lower().startswith('disallow:'):
                    path = line_clean.split(':', 1)[1].strip()
                    if path and path != '/':
                        robots_disallow.append(path)
                        # Add to tree branches
                        seg = path.strip('/').split('/')[0] if '/' in path.strip('/') else path.strip('/')
                        if seg:
                            tree_branches[f"/{seg}"] = "Robots.txt Disallow Rule"
                elif line_clean.lower().startswith('sitemap:'):
                    sm_url = line_clean.split(':', 1)[1].strip()
                    if sm_url:
                        sitemap_candidates.append(sm_url)
    except Exception:
        pass

    # Add default sitemap candidates if not found in robots.txt
    if not sitemap_candidates:
        sitemap_candidates.append(f"{base_url}/sitemap.xml")
        sitemap_candidates.append(f"{base_url}/sitemap_index.xml")

    # 2. Fetch & parse sitemap(s)
    visited_sitemaps = 0
    for sm_url in sitemap_candidates[:3]:
        if visited_sitemaps >= 3 or len(sitemap_urls) >= 400:
            break
        try:
            r_sm = requests.get(sm_url, headers=headers, timeout=12, verify=False)
            if r_sm.status_code == 200 and '<loc>' in r_sm.text:
                visited_sitemaps += 1
                locs = re.findall(r'<loc>\s*(https?://[^<]+)\s*</loc>', r_sm.text, re.IGNORECASE)
                for loc in locs:
                    loc_clean = loc.strip()
                    # If this loc is itself a child sitemap
                    if loc_clean.endswith('.xml') and visited_sitemaps < 3 and loc_clean != sm_url:
                        try:
                            r_sub = requests.get(loc_clean, headers=headers, timeout=10, verify=False)
                            if r_sub.status_code == 200:
                                visited_sitemaps += 1
                                sub_locs = re.findall(r'<loc>\s*(https?://[^<]+)\s*</loc>', r_sub.text, re.IGNORECASE)
                                sitemap_urls.extend(sub_locs[:150])
                        except Exception:
                            pass
                    else:
                        sitemap_urls.append(loc_clean)
        except Exception:
            pass

    # Deduplicate sitemap URLs and build directory tree branches
    sitemap_urls = list(set(sitemap_urls))
    for url in sitemap_urls[:300]:
        path = urllib.parse.urlparse(url).path
        segments = [s for s in path.split('/') if s]
        if segments:
            top_seg = f"/{segments[0]}"
            if top_seg not in tree_branches:
                tree_branches[top_seg] = "Sitemap Directory / Page"

    return {
        "robots_disallow": list(set(robots_disallow)),
        "sitemap_urls": sitemap_urls,
        "tree_branches": tree_branches
    }


def analyze_path_signatures(url_list, disallow_list):
    """
    Analyze discovered sitemap URLs and robots paths for structural CMS & Tech signatures.
    """
    detected = []
    combined_str = " ".join(url_list + disallow_list).lower()

    if 'wp-content/' in combined_str or 'wp-includes/' in combined_str or 'wp-admin' in combined_str or 'post-sitemap.xml' in combined_str:
        detected.append("CMS: WordPress")
    if 'index.php?option=com_' in combined_str or '/administrator/' in combined_str:
        detected.append("CMS: Joomla")
    if '/node/' in combined_str or '/taxonomy/term/' in combined_str:
        detected.append("CMS: Drupal")
    if '/catalog/view/' in combined_str or 'index.php?route=' in combined_str:
        detected.append("E-Commerce: OpenCart")
    if '/collections/' in combined_str or '/products/' in combined_str or 'cdn.shopify.com' in combined_str:
        detected.append("E-Commerce: Shopify")
    if '/_next/' in combined_str or '/static/chunks/' in combined_str:
        detected.append("Frontend Framework: Next.js (React)")
    if '/bitrix/' in combined_str:
        detected.append("CMS: 1C-Bitrix")
    if '/typo3/' in combined_str:
        detected.append("CMS: TYPO3")
    if '/user/login' in combined_str:
        detected.append("Backend Endpoint: User Authentication (/user/login)")
    if '/api/' in combined_str or '/v1/' in combined_str or '/v2/' in combined_str:
        detected.append("Architecture: REST API Endpoints Detected")

    return list(set(detected))


def render_tree_view(tree_branches, sitemap_count, robots_count):
    """Render a clean CLI tree map of discovered site structure."""
    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Site Directory Tree & Structural Map (from Sitemap & Robots.txt):{Colors.RESET}")
    print(f"  {Colors.WHITE}Total Sitemap Pages Discovered: {Colors.CYAN}{sitemap_count}{Colors.RESET} | {Colors.WHITE}Robots Disallow Rules: {Colors.YELLOW}{robots_count}{Colors.RESET}")
    
    if not tree_branches:
        print(f"  {Colors.YELLOW}[!] No structural directory branches discovered via sitemap or robots.txt.{Colors.RESET}")
        return

    sorted_branches = sorted(tree_branches.items(), key=lambda x: x[0])
    max_display = min(25, len(sorted_branches))
    
    for idx, (branch_path, source) in enumerate(sorted_branches[:max_display]):
        prefix = "└── " if idx == max_display - 1 else "├── "
        color = Colors.YELLOW if "Disallow" in source else Colors.CYAN
        print(f"  {prefix}{color}{branch_path:<26}{Colors.RESET} {Colors.WHITE}[{source}]{Colors.RESET}")

    if len(sorted_branches) > max_display:
        print(f"  └── {Colors.YELLOW}... and {len(sorted_branches) - max_display} additional branches.{Colors.RESET}")


def run_technology_detector():
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Web Technology & CMS Fingerprinter (Stack & Site Tree Detector) ---{Colors.RESET}")
    target_url = input(f"{Colors.GREEN}[+] Enter Target URL (e.g. https://example.com): {Colors.RESET}").strip()
    if not target_url:
        return
    if not target_url.startswith('http'):
        target_url = "https://" + target_url

    print(f"{Colors.YELLOW}[*] Sending fingerprint probe and exploring site tree on {target_url}...{Colors.RESET}")
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
    if 'CF-Ray' in h or ('server' in h and 'cloudflare' in h.get('server', '').lower()):
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

    # Site Tree Discovery & Structural Signatures
    tree_data = fetch_site_tree_and_sitemap(target_url)
    path_techs = analyze_path_signatures(tree_data["sitemap_urls"], tree_data["robots_disallow"])
    for pt in path_techs:
        if pt not in techs:
            techs.append(pt)

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Fingerprint Summary for {target_url} (HTTP {resp.status_code}):{Colors.RESET}")
    if techs:
        for t in sorted(list(set(techs))):
            parts = t.split(':', 1)
            if len(parts) == 2:
                print(f"  {Colors.CYAN}{parts[0]:<22}:{Colors.RESET} {Colors.WHITE}{parts[1].strip()}{Colors.RESET}")
            else:
                print(f"  {Colors.YELLOW}[•]{Colors.RESET} {Colors.WHITE}{t}{Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}[!] No specific CMS or stack signatures detected in headers/html.{Colors.RESET}")

    # Render Site Tree View
    render_tree_view(tree_data["tree_branches"], len(tree_data["sitemap_urls"]), len(tree_data["robots_disallow"]))

    if tree_data["sitemap_urls"] or tree_data["robots_disallow"]:
        opt = input(f"\n{Colors.GREEN}[+] Save discovered Site Tree & Sitemap URLs to file? (y/N): {Colors.RESET}").strip().lower()
        if opt.startswith('y'):
            parsed = urllib.parse.urlparse(target_url)
            domain_name = parsed.netloc.replace('www.', '')
            filename = f"sitemap_tree_{domain_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"SITE TREE & SITEMAP DISCOVERY REPORT FOR: {target_url}\n")
                f.write("=" * 65 + "\n\n")
                f.write("=== ROBOTS.TXT DISALLOW RULES ===\n")
                for d in tree_data["robots_disallow"]:
                    f.write(f"Disallow: {d}\n")
                f.write("\n=== TOP-LEVEL DIRECTORY BRANCHES ===\n")
                for b, src in sorted(tree_data["tree_branches"].items()):
                    f.write(f"{b:<30} -> {src}\n")
                f.write("\n=== FULL SITEMAP URL LIST ===\n")
                for u in sorted(tree_data["sitemap_urls"]):
                    f.write(f"{u}\n")
            print(f"{Colors.GREEN}[+] Site Tree report saved to {filename}{Colors.RESET}")

    print(f"\n{Colors.CYAN}[💡 Recommended Action]{Colors.RESET} Based on detected tech and site tree, you can use Option 1 or Option 2 to launch targeted dorks against {target_url}.\n")
