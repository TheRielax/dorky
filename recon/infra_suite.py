# -*- coding: utf-8 -*-
"""
Target Infrastructure, Domain & Web Footprinting Suite.
Combines DNS/WHOIS/SPF audit, Passive Subdomain Enumeration, Web Technology/CMS detection,
and an Automated ALL-IN-ONE Assessment with Subdomain Liveness & Deduplication (Anti-Mirror) checking.
"""

import re
import json
import time
import socket
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
from recon.whois import run_dns_whois_osint
from recon.subdomains import run_subdomain_recon, enumerate_subdomains_passive, clean_domain
from recon.fingerprint import run_technology_detector


def check_subdomain_liveness_and_uniqueness(root_domain, subdomains_list):
    """
    Probe every discovered subdomain for active HTTP/HTTPS web servers and verify whether
    it is a unique target or simply redirects/mirrors to the root domain.
    Returns:
        results_table: list of dicts with {"subdomain": ..., "status": ..., "redirect_url": ..., "is_unique_active": bool}
        unique_active_targets: list of URL strings ready for Site Tree & Tech scanning
    """
    results_table = []
    unique_active_targets = []
    seen_netlocs = set()
    seen_titles = set()
    seen_snippets = set()
    
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    root_clean = clean_domain(root_domain)
    seen_netlocs.add(root_clean)
    seen_netlocs.add(f"www.{root_clean}")
    
    # Pre-fetch root domain response/title to detect exact content mirrors (like www or third-level aliases)
    root_title = ""
    root_text_snippet = ""
    try:
        r_root = requests.get(f"https://{root_clean}", headers=headers, timeout=8, verify=False, allow_redirects=True)
        if r_root.status_code == 200:
            root_text_snippet = r_root.text[:1500].strip()
            if BeautifulSoup:
                soup = BeautifulSoup(r_root.text, 'html.parser')
                root_title = (soup.title.string or "").strip() if soup.title else ""
    except Exception:
        pass

    if root_title:
        seen_titles.add(root_title.lower())
    if root_text_snippet:
        seen_snippets.add(root_text_snippet)

    for idx, sub in enumerate(subdomains_list, 1):
        sub_clean = sub.strip().lower().lstrip('*.')
        print(f"\r{Colors.CYAN}[{idx}/{len(subdomains_list)}]{Colors.RESET} Probing liveness & deduplicating {Colors.WHITE}{sub_clean:<40}{Colors.RESET}...", end="", flush=True)
        
        # Try resolving IP first to skip completely dead DNS hosts quickly
        try:
            ip = socket.gethostbyname(sub_clean)
        except Exception:
            results_table.append({
                "subdomain": sub_clean,
                "status": "OFFLINE (No DNS Record)",
                "redirect_url": "N/A",
                "is_unique_active": False
            })
            continue

        # Try HTTP/HTTPS probe
        probe_url = f"https://{sub_clean}"
        resp = None
        try:
            resp = requests.get(probe_url, headers=headers, timeout=6, verify=False, allow_redirects=True)
        except Exception:
            try:
                probe_url = f"http://{sub_clean}"
                resp = requests.get(probe_url, headers=headers, timeout=6, verify=False, allow_redirects=True)
            except Exception:
                pass

        if not resp or resp.status_code >= 500:
            results_table.append({
                "subdomain": sub_clean,
                "status": "OFFLINE (No Web Server / Timeout)",
                "redirect_url": "N/A",
                "is_unique_active": False
            })
            continue

        final_url = resp.url
        final_netloc = urllib.parse.urlparse(final_url).netloc.lower()
        
        # Check if it redirects straight to root, www.root, or any already processed target host
        if (final_netloc in seen_netlocs or final_netloc in [root_clean, f"www.{root_clean}"]) and sub_clean not in [root_clean, f"www.{root_clean}"] and final_netloc != sub_clean:
            results_table.append({
                "subdomain": sub_clean,
                "status": f"ACTIVE (Redirects to {final_netloc} -> Skipping Duplicate)",
                "redirect_url": final_url,
                "is_unique_active": False
            })
            continue

        # Check if page body or title exact matches root domain or previously seen unique targets
        sub_snippet = resp.text[:1500].strip()
        sub_title = ""
        if BeautifulSoup:
            try:
                s_soup = BeautifulSoup(resp.text, 'html.parser')
                sub_title = (s_soup.title.string or "").strip() if s_soup.title else ""
            except Exception:
                pass
        
        is_mirror = False
        if root_text_snippet and sub_snippet == root_text_snippet:
            is_mirror = True
        elif root_title and sub_title and sub_title.lower() == root_title.lower() and len(sub_title) > 2:
            is_mirror = True
        elif sub_snippet and sub_snippet in seen_snippets:
            is_mirror = True
        elif sub_title and sub_title.lower() in seen_titles and len(sub_title) > 3:
            is_mirror = True
            
        if is_mirror or sub_clean == f"www.{root_clean}":
            results_table.append({
                "subdomain": sub_clean,
                "status": "ACTIVE (Exact Mirror/Alias of Root Domain -> Skipping Duplicate Tree)",
                "redirect_url": final_url,
                "is_unique_active": False
            })
            continue

        # If we reached here, it's an active and unique subdomain!
        seen_netlocs.add(sub_clean)
        seen_netlocs.add(final_netloc)
        if sub_title:
            seen_titles.add(sub_title.lower())
        if sub_snippet:
            seen_snippets.add(sub_snippet)

        results_table.append({
            "subdomain": sub_clean,
            "status": f"ACTIVE (Unique Target - HTTP {resp.status_code})",
            "redirect_url": final_url,
            "is_unique_active": True
        })
        unique_active_targets.append(probe_url)

    print()
    return results_table, unique_active_targets


def run_full_automated_assessment(search_callback=None):
    """
    Automated ALL-IN-ONE Infrastructure, DNS/Security, Passive Subdomains, and Deduplicated Site Tree Assessment.
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("      ⚡ FULL AUTOMATED INFRASTRUCTURE & SITE TREE ASSESSMENT (ALL-IN-ONE)    ")
    print("=============================================================================" + Colors.RESET)
    print(f"{Colors.WHITE}Performs consolidated DNS/WHOIS audit, passive subdomain enumeration, liveness & deduplication checking, and multi-host Site Tree/Tech fingerprinting without duplicate tree noise.{Colors.RESET}\n")

    domain = input(f"{Colors.GREEN}[+] Target Root Domain (e.g. example.com): {Colors.RESET}").strip()
    if not domain:
        return
    domain = clean_domain(domain)

    # STEP 1: DNS, WHOIS & Security Posture
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- [Phase 1/4] DNS, WHOIS & Email Security Audit ({domain}) ---{Colors.RESET}")
    dns_data = run_dns_whois_osint(target=domain, interactive=False)
    
    # STEP 2: Passive Subdomain Enumeration
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- [Phase 2/4] Passive Subdomain Enumeration (*.{domain}) ---{Colors.RESET}")
    subdomains = enumerate_subdomains_passive(domain, quiet=False)
    print(f"{Colors.GREEN}[+] Discovered {len(subdomains)} total subdomains from passive certificate logs.{Colors.RESET}")

    # STEP 3: Liveness & Deduplication Check
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- [Phase 3/4] Subdomain Liveness & Deduplication Analysis ---{Colors.RESET}")
    liveness_table, unique_targets = check_subdomain_liveness_and_uniqueness(domain, subdomains)

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Subdomain Audit Table (Active vs Mirrors/Redirects vs Offline):{Colors.RESET}")
    for item in liveness_table:
        sub = item["subdomain"]
        status = item["status"]
        status_col = Colors.GREEN if item["is_unique_active"] else (Colors.YELLOW if "ACTIVE" in status else Colors.RED)
        print(f"  {Colors.CYAN}{sub:<36}{Colors.RESET} -> {status_col}[{status}]{Colors.RESET}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Summary: {len(liveness_table)} subdomains audited | {len(unique_targets)} unique active subdomains identified for Site Tree assessment.{Colors.RESET}")

    # STEP 4: Web Technology & Site Tree Fingerprinting
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- [Phase 4/4] Web Technology, CMS & Site Tree Fingerprinting ---{Colors.RESET}")
    
    all_fingerprints = {}
    seen_tree_keys = {}
    
    # First, always scan Root Domain
    root_url = f"https://{domain}"
    print(f"\n{Colors.YELLOW}[*] Fingerprinting Root Domain: {root_url}...{Colors.RESET}")
    root_fp = run_technology_detector(target_url=root_url, interactive=False)
    if root_fp:
        all_fingerprints[root_url] = root_fp
        root_branches = tuple(sorted(root_fp.get('tree_data', {}).get('tree_branches', {}).keys()))
        if root_branches:
            seen_tree_keys[root_branches] = root_url

    # Next, scan unique active subdomains (up to 15 to keep execution rapid and respectful)
    for idx, t_url in enumerate(unique_targets[:15], 1):
        # Skip if t_url exactly matches root_url
        if clean_domain(t_url) == clean_domain(root_url):
            continue
        print(f"\n{Colors.YELLOW}[*] Fingerprinting Unique Subdomain [{idx}/{len(unique_targets[:15])}]: {t_url}...{Colors.RESET}")
        fp = run_technology_detector(target_url=t_url, interactive=False)
        if fp:
            branches_tuple = tuple(sorted(fp.get('tree_data', {}).get('tree_branches', {}).keys()))
            if branches_tuple and branches_tuple in seen_tree_keys:
                fp['is_duplicate_tree'] = True
                fp['duplicate_of'] = seen_tree_keys[branches_tuple]
            else:
                fp['is_duplicate_tree'] = False
                if branches_tuple:
                    seen_tree_keys[branches_tuple] = t_url
            all_fingerprints[t_url] = fp
            time.sleep(0.3)

    # STEP 5: Consolidated Summary & Export
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print(f"            CONSOLIDATED INFRASTRUCTURE ASSESSMENT REPORT ({domain.upper()})")
    print("=============================================================================" + Colors.RESET)
    
    if dns_data:
        print(f"  {Colors.WHITE}Registrar:{Colors.RESET} {Colors.CYAN}{dns_data.get('registrar')}{Colors.RESET} | {Colors.WHITE}IPv4:{Colors.RESET} {Colors.CYAN}{', '.join(dns_data.get('ipv4_addrs', [])[:3])}{Colors.RESET}")
        print(f"  {Colors.WHITE}SPF Posture:{Colors.RESET} {dns_data.get('spf_policy')} | {Colors.WHITE}DMARC Posture:{Colors.RESET} {dns_data.get('dmarc_policy')}")
        if dns_data.get('reg_lines'):
            for k, v in dns_data['reg_lines']:
                if k:
                    print(f"  {Colors.WHITE}Registrant {k}:{Colors.RESET} {Colors.YELLOW}{v}{Colors.RESET}")
                elif v:
                    print(f"  {Colors.WHITE}Registrant Details:{Colors.RESET} {Colors.YELLOW}{v}{Colors.RESET}")
    
    print(f"  {Colors.WHITE}Subdomains Discovered:{Colors.RESET} {len(subdomains)} | {Colors.WHITE}Unique Active Hosts Analyzed:{Colors.RESET} {len(all_fingerprints)}")

    for target_u, fp_data in all_fingerprints.items():
        print(f"\n  {Colors.GREEN}[+] Host: {Colors.WHITE}{Colors.BOLD}{target_u}{Colors.RESET} {Colors.MAGENTA}(HTTP {fp_data['status_code']}){Colors.RESET}")
        if fp_data['technologies']:
            print(f"      {Colors.YELLOW}Stack:{Colors.RESET} {', '.join(fp_data['technologies'][:6])}")
        
        if fp_data.get('is_duplicate_tree'):
            dup_target = fp_data.get('duplicate_of', f'https://{domain}')
            print(f"      {Colors.CYAN}Site Tree & Sitemap:{Colors.RESET} {Colors.YELLOW}[IDENTICAL TO {dup_target} -> Directory branches and sitemaps omitted to prevent duplicate repetition]{Colors.RESET}")
        else:
            tree_info = fp_data.get('tree_data', {})
            sm_count = len(tree_info.get('sitemap_urls', []))
            rb_count = len(tree_info.get('robots_disallow', []))
            br_count = len(tree_info.get('tree_branches', {}))
            print(f"      {Colors.CYAN}Site Tree:{Colors.RESET} {sm_count} sitemap URLs | {rb_count} disallow rules | {br_count} directory branches")

    opt = input(f"\n{Colors.GREEN}[+] Save ALL-IN-ONE Infrastructure Assessment report to JSON & TXT? (y/N): {Colors.RESET}").strip().lower()
    if opt.startswith('y'):
        ts_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"infra_assessment_{domain}_{ts_str}.json"
        txt_file = f"infra_assessment_{domain}_{ts_str}.txt"

        json_export = {
            "root_domain": domain,
            "timestamp": ts_str,
            "dns_whois": dns_data,
            "subdomains_audit": liveness_table,
            "fingerprints_and_site_trees": all_fingerprints
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_export, f, indent=2, ensure_ascii=False)

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"FULL AUTOMATED INFRASTRUCTURE ASSESSMENT FOR: {domain}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 75 + "\n\n")
            if dns_data:
                f.write("=== PHASE 1: DNS, WHOIS & SECURITY POSTURE ===\n")
                f.write(f"Registrar: {dns_data.get('registrar')}\n")
                f.write(f"Created / Expiry: {dns_data.get('creation_date')} -> {dns_data.get('expiry_date')}\n")
                f.write(f"IPv4 Addresses: {', '.join(dns_data.get('ipv4_addrs', []))}\n")
                f.write(f"SPF Policy: {dns_data.get('spf_policy')}\n")
                f.write(f"DMARC Policy: {dns_data.get('dmarc_policy')}\n")
                if dns_data.get('reg_lines'):
                    f.write("\n--- WHOIS Registrant Summary ---\n")
                    for k, v in dns_data['reg_lines']:
                        f.write(f"  {k}: {v}\n" if k else f"  {v}\n")
                elif dns_data.get('org'):
                    f.write(f"\nOrganization: {dns_data.get('org')}\n")
                if dns_data.get('admin_lines'):
                    f.write("\n--- WHOIS Administrative Contact ---\n")
                    for k, v in dns_data['admin_lines']:
                        f.write(f"  {k}: {v}\n" if k else f"  {v}\n")
                if dns_data.get('tech_lines'):
                    f.write("\n--- WHOIS Technical Contact ---\n")
                    for k, v in dns_data['tech_lines']:
                        f.write(f"  {k}: {v}\n" if k else f"  {v}\n")
                if dns_data.get('raw_text'):
                    f.write("\n--- COMPLETE RAW WHOIS RECORD OUTPUT ---\n")
                    f.write(dns_data['raw_text'] + "\n")
                f.write("\n")
            
            f.write("=== PHASE 2 & 3: SUBDOMAIN LIVENESS & DEDUPLICATION AUDIT ===\n")
            for item in liveness_table:
                f.write(f"{item['subdomain']:<38} -> {item['status']} (Redirect: {item['redirect_url']})\n")
            f.write("\n")

            f.write("=== PHASE 4: WEB TECHNOLOGY & SITE TREE FINGERPRINTS ===\n")
            for target_u, fp_data in all_fingerprints.items():
                f.write(f"--- Host: {target_u} (HTTP {fp_data['status_code']}) ---\n")
                for t in fp_data['technologies']:
                    f.write(f"  * Tech: {t}\n")
                
                if fp_data.get('is_duplicate_tree'):
                    dup_target = fp_data.get('duplicate_of', f'https://{domain}')
                    f.write(f"  * Site Tree & Sitemap: [IDENTICAL TO {dup_target} -> Directory branches and sitemaps omitted to prevent duplicate repetition]\n\n")
                else:
                    tree_info = fp_data.get('tree_data', {})
                    f.write("  * Robots Disallow Rules:\n")
                    for r in tree_info.get('robots_disallow', []):
                        f.write(f"      Disallow: {r}\n")
                    f.write("  * Directory Tree Branches:\n")
                    for b, src in sorted(tree_info.get('tree_branches', {}).items()):
                        f.write(f"      {b:<30} -> {src}\n")
                    f.write("  * Sitemap URLs (sample):\n")
                    for u in sorted(tree_info.get('sitemap_urls', []))[:50]:
                        f.write(f"      {u}\n")
                    f.write("\n")

        print(f"{Colors.GREEN}[+] Consolidated reports saved successfully to:\n    - {json_file}\n    - {txt_file}{Colors.RESET}")


def run_infrastructure_suite(search_callback=None):
    """
    Submenu for Target Infrastructure, Domain & Web Footprinting Suite.
    """
    while True:
        print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
        print("             TARGET INFRASTRUCTURE, DOMAIN & WEB FOOTPRINTING SUITE          ")
        print("=============================================================================" + Colors.RESET)
        print(f"  {Colors.CYAN}[1]{Colors.RESET} Domain DNS, WHOIS & Security Posture (SPF/DMARC)")
        print(f"  {Colors.CYAN}[2]{Colors.RESET} Passive Subdomain Enumeration (CRT.sh & Certificate Logs)")
        print(f"  {Colors.CYAN}[3]{Colors.RESET} Web Technology, CMS & Site Tree Fingerprinter")
        print(f"  {Colors.GREEN}{Colors.BOLD}[4] ⚡ Full Automated Infrastructure & Site Tree Assessment (ALL-IN-ONE){Colors.RESET}")
        print(f"  {Colors.YELLOW}[0]{Colors.RESET} Return to Main Menu")

        choice = input(f"\n{Colors.GREEN}[+] Select Option (0-4): {Colors.RESET}").strip()

        if choice == "1":
            query = run_dns_whois_osint(interactive=True)
            if query and search_callback:
                search_callback(query)
            input(f"\n{Colors.YELLOW}Press Enter to return to Infrastructure Suite menu...{Colors.RESET}")
        elif choice == "2":
            run_subdomain_recon(search_callback=search_callback)
            input(f"\n{Colors.YELLOW}Press Enter to return to Infrastructure Suite menu...{Colors.RESET}")
        elif choice == "3":
            run_technology_detector(interactive=True)
            input(f"\n{Colors.YELLOW}Press Enter to return to Infrastructure Suite menu...{Colors.RESET}")
        elif choice == "4":
            run_full_automated_assessment(search_callback=search_callback)
            input(f"\n{Colors.YELLOW}Press Enter to return to Infrastructure Suite menu...{Colors.RESET}")
        elif choice == "0" or choice == "":
            break
        else:
            print(f"\n{Colors.RED}[!] Invalid choice. Please select 0-4.{Colors.RESET}")
