#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DORKY - Advanced Multi-Engine Google Dorking & Passive Reconnaissance Tool
Version: 1.0 (Modular Architecture)
Author: Paolo Marco Riela (INNONATION R&D)
"""

import sys
import os
import time
import random

from core.config import Colors, ConfigManager, print_banner
from core.adapter import DorkAdapter
from core.history import HistoryManager, save_results
from engines.search import SearchEngines

from recon.subdomains import run_subdomain_recon
from recon.wayback import run_wayback_recon
from recon.github import run_github_dorking
from recon.fingerprint import run_technology_detector
from recon.phone import run_phone_osint
from recon.email import run_email_osint
from recon.username import run_username_osint
from recon.whois import run_dns_whois_osint


class DorkBuilder:
    """
    Interactive menu to construct customized dork strings.
    """
    @staticmethod
    def run():
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Interactive Dork Query Builder ---{Colors.RESET}")
        site = input(f"{Colors.GREEN}[+] Target Domain / Site (e.g., example.com): {Colors.RESET}").strip()
        inurl = input(f"{Colors.GREEN}[+] URL Contains (inurl - e.g., admin, login, wp-content): {Colors.RESET}").strip()
        intitle = input(f"{Colors.GREEN}[+] Title Contains (intitle - e.g., index of, dashboard): {Colors.RESET}").strip()
        filetype = input(f"{Colors.GREEN}[+] File Extension (filetype - e.g., env, sql, pdf, log): {Colors.RESET}").strip()
        intext = input(f"{Colors.GREEN}[+] Page Body Contains Exact Phrase (intext - e.g., \"password\"): {Colors.RESET}").strip()
        exclude = input(f"{Colors.GREEN}[+] Words to Exclude (comma separated - e.g., help, sample): {Colors.RESET}").strip()

        dork_parts = []
        if site:
            dork_parts.append(f"site:{site}")
        if inurl:
            dork_parts.append(f"inurl:{inurl}")
        if intitle:
            if " " in intitle and not intitle.startswith('"'):
                dork_parts.append(f'intitle:"{intitle}"')
            else:
                dork_parts.append(f"intitle:{intitle}")
        if filetype:
            dork_parts.append(f"filetype:{filetype.lstrip('.')}")
        if intext:
            if not intext.startswith('"'):
                dork_parts.append(f'"{intext}"')
            else:
                dork_parts.append(intext)
        if exclude:
            for ex in exclude.split(','):
                ex_clean = ex.strip()
                if ex_clean:
                    dork_parts.append(f"-{ex_clean}")

        generated_query = " ".join(dork_parts)
        if not generated_query:
            print(f"{Colors.YELLOW}[!] No fields provided. Using generic test query.{Colors.RESET}")
            generated_query = 'intitle:"index of"'

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


def show_syntax_guide():
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("                 SEARCH ENGINE DORK SYNTAX ADAPTATION GUIDE                  ")
    print("=============================================================================" + Colors.RESET)
    guide = [
        ("Google", "site:, filetype:/ext:, intitle:, allintitle:, inurl:, allinurl:, intext:, allintext:, \"\", -, OR"),
        ("DuckDuckGo", "site:, filetype:, intitle:, inurl:, inbody: (adapted from intext/allintext)"),
        ("Bing", "site:, filetype:, intitle:, inurl:, inbody: (adapted from intext/allintext)"),
        ("Brave Search", "site:, filetype:, intitle:, inurl: (intext/allintext converted to keywords)"),
        ("Yandex", "site:, mime: (adapted from filetype/ext), title:, url: (intext stripped)")
    ]
    for engine, syntax in guide:
        print(f"{Colors.BOLD}{Colors.MAGENTA}{engine:<18}{Colors.RESET} : {syntax}")
    print(f"{Colors.CYAN}============================================================================={Colors.RESET}\n")
    input(f"{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")


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
            print(f"  {Colors.CYAN}[12]{Colors.RESET} Email Address OSINT & Breach Footprinting")
            print(f"  {Colors.CYAN}[13]{Colors.RESET} Username & Social Cross-Platform Footprinting")
            print(f"  {Colors.CYAN}[14]{Colors.RESET} Domain DNS, WHOIS & Security Posture (SPF/DMARC)")
            print(f"  {Colors.BOLD}{Colors.MAGENTA}[-- Settings & Exit --]{Colors.RESET}")
            print(f"  {Colors.CYAN}[15]{Colors.RESET} Official API Keys Configuration (Google, Brave, GitHub)")
            print(f"  {Colors.CYAN}[16]{Colors.RESET} Exit")

            choice = input(f"\n{Colors.GREEN}[+] Select Option (1-16): {Colors.RESET}").strip()

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
                run_subdomain_recon(search_callback=run_search_session)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "8":
                run_wayback_recon()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "9":
                run_github_dorking()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "10":
                run_technology_detector()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "11":
                query = run_phone_osint()
                if query:
                    run_search_session(query)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "12":
                query = run_email_osint()
                if query:
                    run_search_session(query)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "13":
                query = run_username_osint()
                if query:
                    run_search_session(query)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "14":
                query = run_dns_whois_osint()
                if query:
                    run_search_session(query)
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "15":
                ConfigManager.configure_interactive()
                input(f"\n{Colors.YELLOW}Press Enter to return to main menu...{Colors.RESET}")
            elif choice == "16":
                print(f"\n{Colors.GREEN}{Colors.BOLD}[*] Thank you for using DORKY! Happy hunting!{Colors.RESET}\n")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}[!] Invalid selection. Please choose between 1 and 16.{Colors.RESET}\n")
                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.RED}{Colors.BOLD}[!] Session interrupted by user. Exiting DORKY...{Colors.RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
