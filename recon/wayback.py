# -*- coding: utf-8 -*-
"""
Wayback Machine historical archive mining module (CDX Explorer & Deep Content Scraper).
"""

import os
import re
import json
import random
import time
import urllib.parse
from datetime import datetime

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from core.config import Colors, USER_AGENTS
from recon.subdomains import clean_domain


PATHS_BY_CATEGORY = {
    "Contacts, Team & About (IT/EN)": [
        "/", "/about", "/about-us", "/who-we-are", "/team", "/management",
        "/leadership", "/board", "/chi-siamo", "/azienda", "/storia",
        "/contatti", "/contact", "/contact-us", "/lavora-con-noi", "/careers"
    ],
    "Partners & Clients (IT/EN)": [
        "/partners", "/partner", "/clients", "/clienti", "/customers",
        "/case-studies", "/referenze", "/references", "/portfolio",
        "/testimoni", "/testimonials", "/collaborazioni", "/network"
    ],
    "Products, Services & Projects (IT/EN)": [
        "/products", "/prodotti", "/services", "/servizi", "/projects",
        "/progetti", "/soluzioni", "/solutions", "/catalog", "/catalogo",
        "/offerta", "/offering"
    ]
}


def format_timestamp(ts):
    """Format a 14-digit Wayback timestamp to YYYY-MM-DD."""
    if not ts or len(ts) < 8:
        return str(ts)
    return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"


def filter_cdx_endpoints(rows, inurl_kws, exclude_kws, filetypes, status_codes):
    """
    Filter CDX JSON rows across URL keywords (inurl), exclusion keywords (-exclude),
    file extensions (filetype), and HTTP status codes (status).
    Returns a list of tuples: (orig_url, formatted_timestamp, statuscode, mimetype, raw_ts, snapshot_url).
    """
    if not rows or len(rows) <= 1:
        return []

    headers = {h: idx for idx, h in enumerate(rows[0])}
    idx_orig = headers.get("original", 0)
    idx_ts = headers.get("timestamp", 1)
    idx_status = headers.get("statuscode", 2) if "statuscode" in headers else -1
    idx_mime = headers.get("mimetype", 3) if "mimetype" in headers else -1

    results = []
    for row in rows[1:]:
        try:
            orig_url = row[idx_orig]
            ts = row[idx_ts]
            status = str(row[idx_status]) if idx_status != -1 else "N/A"
            mime = str(row[idx_mime]) if idx_mime != -1 else "N/A"
            
            url_lower = orig_url.lower()
            parsed_path = urllib.parse.urlparse(orig_url).path.lower()

            # 1. Check -exclude keywords
            if exclude_kws and any(ex in url_lower for ex in exclude_kws):
                continue

            # 2. Check inurl keywords (if specified, at least one must match)
            if inurl_kws and not any(kw in url_lower for kw in inurl_kws):
                continue

            # 3. Check file extensions (if specified and not 'all')
            if filetypes and "all" not in filetypes:
                if not any(parsed_path.endswith(f".{ft}") for ft in filetypes):
                    continue

            # 4. Check status codes (if specified and not 'all')
            if status_codes and "all" not in status_codes:
                if not any(sc == status for sc in status_codes):
                    continue

            snapshot_url = f"https://web.archive.org/web/{ts}/{orig_url}"
            results.append((orig_url, format_timestamp(ts), status, mime, ts, snapshot_url))
        except Exception:
            continue

    return results


def grep_snapshot_content(ts, orig_url, intext_kw):
    """
    Download a Wayback snapshot body using id_ modifier (raw content) and search for intext keyword/pattern.
    Returns matching snippet around the keyword if found, or None.
    """
    if not requests or not BeautifulSoup:
        return None

    raw_archive_url = f"http://web.archive.org/web/{ts}id_/{orig_url}"
    try:
        resp = requests.get(raw_archive_url, timeout=12, headers={'User-Agent': random.choice(USER_AGENTS)})
        if resp.status_code == 200:
            text = resp.text
            match = re.search(re.escape(intext_kw), text, re.IGNORECASE)
            if not match:
                try:
                    match = re.search(intext_kw, text, re.IGNORECASE)
                except Exception:
                    pass
            
            if match:
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 60)
                snippet = text[start:end].replace('\n', ' ').replace('\r', ' ')
                snippet = re.sub(r'\s+', ' ', snippet).strip()
                return snippet
    except Exception:
        pass
    return None


def run_wayback_cdx_dork_builder(domain):
    """Interactive CDX Dork Builder (`CDX Dorking & Historical Content Search`)."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Wayback CDX Interactive Dork Builder & Archive Search ---{Colors.RESET}")
    print(f"{Colors.WHITE}Construct targeted Boolean/filter dorks across Internet Archive CDX historical snapshots.{Colors.RESET}\n")

    inurl_input = input(f"{Colors.GREEN}[1] URL Keywords (`inurl:`, comma-separated, e.g. admin, login, api, config, backup) [press Enter for ALL]: {Colors.RESET}").strip()
    inurl_kws = [k.strip().lower() for k in inurl_input.split(',') if k.strip()]

    ex_input = input(f"{Colors.GREEN}[2] Exclude Keywords (`-exclude`, comma-separated, e.g. wp-includes, bootstrap, jquery) [press Enter to skip]: {Colors.RESET}").strip()
    exclude_kws = [k.strip().lower() for k in ex_input.split(',') if k.strip()]

    ft_input = input(f"{Colors.GREEN}[3] File Extensions (`filetype:`, comma-separated, e.g. env, sql, conf, log, bak, zip, pdf) [default: ALL]: {Colors.RESET}").strip()
    filetypes = [f.strip().lower().lstrip('.') for f in ft_input.split(',') if f.strip()] if ft_input else ["all"]

    sc_input = input(f"{Colors.GREEN}[4] HTTP Status Codes (`status:`, comma-separated, e.g. 200, 403, 301) [default: ALL]: {Colors.RESET}").strip()
    status_codes = [s.strip() for s in sc_input.split(',') if s.strip()] if sc_input else ["all"]

    from_year = input(f"{Colors.GREEN}[5] Start Year (`from:`, e.g. 2016) [press Enter for all time]: {Colors.RESET}").strip()
    to_year = input(f"{Colors.GREEN}[6] End Year (`to:`, e.g. 2023) [press Enter for all time]: {Colors.RESET}").strip()

    intext_kw = input(f"{Colors.GREEN}[7] Historical Content Grep (`intext:`, keyword/regex inside archived pages, e.g. API_KEY, password) [press Enter to skip]: {Colors.RESET}").strip()

    print(f"\n{Colors.YELLOW}[*] Building CDX query & fetching historical archive index for *.{domain}...{Colors.RESET}")
    
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original,timestamp,statuscode,mimetype&collapse=urlkey&limit=1500"
    if from_year and from_year.isdigit():
        cdx_url += f"&from={from_year}"
    if to_year and to_year.isdigit():
        cdx_url += f"&to={to_year}"

    try:
        resp = requests.get(cdx_url, timeout=20, headers={'User-Agent': random.choice(USER_AGENTS)})
        if resp.status_code != 200:
            print(f"{Colors.RED}[!] CDX API returned HTTP {resp.status_code}{Colors.RESET}")
            return
        rows = resp.json()
    except Exception as e:
        print(f"{Colors.RED}[!] CDX API query failed: {e}{Colors.RESET}")
        return

    filtered = filter_cdx_endpoints(rows, inurl_kws, exclude_kws, filetypes, status_codes)
    print(f"{Colors.GREEN}{Colors.BOLD}[+] Found {len(filtered)} historical endpoints matching CDX Dork criteria.{Colors.RESET}")

    if not filtered:
        print(f"{Colors.YELLOW}[!] No historical endpoints matched the specified dork criteria.{Colors.RESET}")
        return

    for idx, (orig_url, fmt_ts, status, mime, raw_ts, snap_url) in enumerate(filtered[:50], 1):
        status_col = Colors.GREEN if status == "200" else (Colors.RED if status in ["403", "401"] else Colors.YELLOW)
        print(f"  {Colors.CYAN}[{fmt_ts}]{Colors.RESET} {status_col}[{status:<3}]{Colors.RESET} {Colors.WHITE}{snap_url:<75}{Colors.RESET} {Colors.MAGENTA}({mime}){Colors.RESET}")
        print(f"     {Colors.YELLOW}-> Target Path: {orig_url}{Colors.RESET}")

    if len(filtered) > 50:
        print(f"{Colors.YELLOW}... and {len(filtered) - 50} more endpoints.{Colors.RESET}")

    intext_matches = []
    if intext_kw:
        target_snaps = [f for f in filtered if f[2] == "200"][:40]
        if target_snaps:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}[*] Launching Historical Content Grep (`intext:{intext_kw}`) across {len(target_snaps)} snapshots...{Colors.RESET}")
            for idx, (orig_url, fmt_ts, status, mime, raw_ts, snap_url) in enumerate(target_snaps, 1):
                print(f"\r{Colors.CYAN}[{idx}/{len(target_snaps)}]{Colors.RESET} Grepping {Colors.WHITE}{orig_url[:50]:<50}{Colors.RESET}...", end="", flush=True)
                snippet = grep_snapshot_content(raw_ts, orig_url, intext_kw)
                if snippet:
                    intext_matches.append((orig_url, fmt_ts, snippet, snap_url))
                time.sleep(0.3)
            print()

            if intext_matches:
                print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Historical Content Grep identified {len(intext_matches)} snapshots containing '{intext_kw}':{Colors.RESET}")
                for u, t, snip, snap_u in intext_matches:
                    print(f"  {Colors.RED}[MATCH @ {t}]{Colors.RESET} {Colors.WHITE}{snap_u}{Colors.RESET}")
                    print(f"    {Colors.CYAN}Target Path: {u}{Colors.RESET}")
                    print(f"    {Colors.YELLOW}Snippet: \"...{snip}...\"{Colors.RESET}\n")
            else:
                print(f"\n{Colors.YELLOW}[!] No historical content matches found for '{intext_kw}' in the sampled snapshots.{Colors.RESET}")

    opt = input(f"\n{Colors.GREEN}[+] Save CDX Dorking results to TXT & JSON reports? (y/N): {Colors.RESET}").strip().lower()
    if opt.startswith('y'):
        ts_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        txt_file = f"cdx_dork_{domain}_{ts_str}.txt"
        json_file = f"cdx_dork_{domain}_{ts_str}.json"

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"WAYBACK CDX DORKING REPORT FOR: {domain}\n")
            f.write(f"Dork Criteria: inurl={inurl_kws} | -exclude={exclude_kws} | filetype={filetypes} | status={status_codes} | from/to={from_year}-{to_year} | intext={intext_kw}\n")
            f.write("=" * 80 + "\n\n")
            f.write("=== MATCHING HISTORICAL SNAPSHOTS ===\n")
            for orig_url, fmt_ts, status, mime, raw_ts, snap_url in filtered:
                f.write(f"[{fmt_ts}] [HTTP {status}] ({mime}) {snap_url}\n  Original Target: {orig_url}\n")
            
            if intext_matches:
                f.write("\n=== INTEXT HISTORICAL CONTENT MATCHES ===\n")
                for u, t, snip, snap_u in intext_matches:
                    f.write(f"[{t}] {snap_u}\n  Original Target: {u}\n  Snippet: \"...{snip}...\"\n\n")

        json_data = {
            "domain": domain,
            "timestamp": ts_str,
            "dork_criteria": {
                "inurl": inurl_kws,
                "exclude": exclude_kws,
                "filetypes": filetypes,
                "status_codes": status_codes,
                "date_range": [from_year, to_year],
                "intext": intext_kw
            },
            "endpoints_count": len(filtered),
            "endpoints": [
                {"snapshot_url": snap_url, "original_url": u, "date": t, "status": s, "mime": m} for u, t, s, m, r, snap_url in filtered
            ],
            "intext_matches": [
                {"snapshot_url": snap_u, "original_url": u, "date": t, "snippet": snip} for u, t, snip, snap_u in intext_matches
            ]
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"{Colors.GREEN}[+] Reports saved successfully to:\n    - {txt_file}\n    - {json_file}{Colors.RESET}")


def discover_historical_site_tree(domain):
    """
    Query CDX Global Index for unique historical paths ever recorded on *.domain.
    """
    api_url = (
        f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json"
        f"&fl=original,statuscode&filter=statuscode:200&collapse=urlkey&limit=1500"
    )
    try:
        resp = requests.get(api_url, timeout=20, headers={'User-Agent': random.choice(USER_AGENTS)})
        if resp.status_code != 200:
            return []
        rows = resp.json()
        if not rows or len(rows) <= 1:
            return []

        unique_paths = set()
        skip_exts = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js", ".woff", ".woff2", ".ico", ".pdf", ".zip")
        for row in rows[1:]:
            orig = row[0]
            parsed = urllib.parse.urlparse(orig)
            path = parsed.path
            if path and not any(path.lower().endswith(x) for x in skip_exts):
                unique_paths.add(path)

        return sorted(list(unique_paths))
    except Exception:
        return []


def classify_url_category(url_path):
    """
    Dynamically classify a historical URL path into target intelligence categories.
    """
    path_lower = url_path.lower()
    
    if path_lower == "/" or path_lower == "":
        return "Contacts, Team & About (IT/EN)"

    if any(kw in path_lower for kw in ["about", "chi-siamo", "team", "management", "board", "leadership", "cda", "storia", "azienda", "contatti", "contact", "careers", "lavora-con-noi", "people", "governance", "staff", "soci", "fondatori", "il-gruppo", "nostra-realt"]):
        return "Contacts, Team & About (IT/EN)"
    elif any(kw in path_lower for kw in ["partner", "clienti", "client", "customer", "case-stud", "referenz", "reference", "portfolio", "testimon", "collaborazioni", "network", "clienti-e-mercati", "accreditam"]):
        return "Partners & Clients (IT/EN)"
    elif any(kw in path_lower for kw in ["product", "prodott", "service", "serviz", "project", "progett", "soluzion", "solution", "catalog", "offerta", "schede", "item", "realizzazioni"]):
        return "Products, Services & Projects (IT/EN)"
    
    return None


def fetch_historical_snapshots(domain, path, limit_per_year=1, start_year=None):
    """
    Query CDX API for statuscode 200 snapshots, collapsed by SHA1 digest,
    returning at most `limit_per_year` unique snapshots per year.
    """
    target_url = f"{domain.rstrip('/')}{path}"
    api_url = (
        f"http://web.archive.org/cdx/search/cdx?url={urllib.parse.quote(target_url)}&output=json"
        f"&fl=timestamp,original,digest,statuscode&filter=statuscode:200&collapse=digest"
    )
    try:
        resp = requests.get(api_url, timeout=15, headers={'User-Agent': random.choice(USER_AGENTS)})
        if resp.status_code != 200:
            return []
        rows = resp.json()
        if not rows or len(rows) <= 1:
            return []
        
        snapshots_by_year = {}
        for row in rows[1:]:
            ts, orig, digest, status = row[0], row[1], row[2], row[3]
            year = ts[:4]
            if start_year and int(year) < int(start_year):
                continue
            if year not in snapshots_by_year:
                snapshots_by_year[year] = []
            if len(snapshots_by_year[year]) < limit_per_year:
                snapshots_by_year[year].append((ts, orig, digest))
                
        return [item for sub in sorted(snapshots_by_year.items()) for item in sub[1]]
    except Exception:
        return []


def extract_partners_and_clients(soup, url_path):
    """Semantic HTML extraction of partner/client mentions or logos."""
    results = set()
    keywords = ["partner", "client", "cliente", "customer", "case-stud", "referenz", "collaborat", "logo", "portfolio", "testimon"]
    
    # 1. Look for images with alt/title mentioning client/partner or inside class/id container
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        title = (img.get("title") or "").strip()
        src = (img.get("src") or "").lower()
        if any(kw in alt.lower() or kw in title.lower() for kw in keywords) or ("logo" in src and len(alt) > 2):
            if alt and len(alt) < 60 and not any(skip in alt.lower() for skip in ["banner", "icon", "arrow", "menu"]):
                results.add(alt)
        elif any(kw in url_path.lower() for kw in ["partner", "client", "referenz", "case-stud"]):
            if alt and 2 < len(alt) < 50:
                results.add(alt)

    # 2. Look inside containers (<section>, <div>, <ul>) whose class or ID matches keywords
    for container in soup.find_all(["section", "div", "ul", "table"]):
        c_id = (container.get("id") or "").lower()
        c_class = " ".join(container.get("class") or []).lower()
        if any(kw in c_id or kw in c_class for kw in keywords):
            # Extract heading or list item texts
            for elem in container.find_all(["h2", "h3", "h4", "li", "strong"]):
                text = elem.get_text(strip=True)
                if 2 < len(text) < 70 and not text.lower().startswith("scopri") and not text.lower().startswith("leggi"):
                    results.add(text)

    return list(results)


def extract_products_and_projects(soup, url_path):
    """Semantic HTML extraction of products, solutions or project names."""
    results = set()
    keywords = ["product", "prodotto", "service", "servizio", "project", "progetto", "solution", "soluzione", "catalog", "offerta", "card"]

    # If the page itself is a dedicated category URL (/products, /progetti, etc.)
    is_category_url = any(kw in url_path.lower() for kw in ["prodott", "product", "serviz", "service", "progett", "project", "soluzion", "solution"])

    # 1. Look inside cards or service containers
    for container in soup.find_all(["div", "section", "article"]):
        c_id = (container.get("id") or "").lower()
        c_class = " ".join(container.get("class") or []).lower()
        if any(kw in c_id or kw in c_class for kw in keywords) or is_category_url:
            for heading in container.find_all(["h2", "h3", "h4"]):
                h_text = heading.get_text(strip=True)
                if 2 < len(h_text) < 65 and not any(x in h_text.lower() for x in ["contatt", "about", "home", "menu", "search"]):
                    results.add(h_text)

    return list(results)


def harvest_snapshot_data(timestamp, original_url):
    """Fetch raw HTML for snapshot using id_ modifier and extract entities."""
    raw_url = f"http://web.archive.org/web/{timestamp}id_/{original_url}"
    try:
        r = requests.get(raw_url, timeout=15, headers={'User-Agent': random.choice(USER_AGENTS)})
        if r.status_code != 200:
            return None
            
        if not BeautifulSoup:
            return None

        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Remove scripts, styles, navigation, and footers
        for elem in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            elem.decompose()
            
        clean_text = soup.get_text(separator=' ', strip=True)
        url_path = urllib.parse.urlparse(original_url).path

        # Regex extractors
        emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', clean_text))
        phones = set(re.findall(r'(?:\+39|0039)?\s*(?:0\d{1,3}[\s-]*\d{5,8}|3\d{2}[\s-]*\d{6,7})', clean_text))
        piva = set(re.findall(r'\b(?:P\.?\s*IVA|Partita\s*Iva|P\.I\.?|C\.F\.?|Codice\s*Fiscale)\s*:?\s*([A-Z0-9]{11,16})\b', clean_text, re.IGNORECASE))
        analytics = set(re.findall(r'\b(UA-\d+-\d+|G-[A-Z0-9]{8,12})\b', r.text))

        # Semantic extractors
        partners = extract_partners_and_clients(soup, url_path)
        products = extract_products_and_projects(soup, url_path)

        return {
            "timestamp": timestamp,
            "formatted_date": format_timestamp(timestamp),
            "url": original_url,
            "path": url_path,
            "emails": list(emails),
            "phones": list(phones),
            "piva": list(piva),
            "analytics_ids": list(analytics),
            "partners_clients": partners,
            "products_projects": products
        }
    except Exception:
        return None


def update_timeline(timeline_dict, items, snapshot_date, path):
    """Aggregate entity items into historical timeline registry."""
    for item in items:
        item_clean = item.strip()
        if not item_clean or len(item_clean) < 3:
            continue
        if item_clean not in timeline_dict:
            timeline_dict[item_clean] = {
                "first_seen": snapshot_date,
                "last_seen": snapshot_date,
                "paths": set([path])
            }
        else:
            if snapshot_date < timeline_dict[item_clean]["first_seen"]:
                timeline_dict[item_clean]["first_seen"] = snapshot_date
            if snapshot_date > timeline_dict[item_clean]["last_seen"]:
                timeline_dict[item_clean]["last_seen"] = snapshot_date
            timeline_dict[item_clean]["paths"].add(path)


def run_wayback_deep_harvesting(domain):
    """Deep Content & Corporate Intelligence Harvesting mode."""
    if not requests or not BeautifulSoup:
        print(f"{Colors.RED}[!] 'requests' or 'beautifulsoup4' is required for Deep Harvesting. Check requirements.txt.{Colors.RESET}")
        return

    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Deep Content & Corporate Intelligence Harvesting ---{Colors.RESET}")
    print(f"{Colors.WHITE}Scans paths across IT/EN for Contacts, Partners/Clients, and Products/Projects.{Colors.RESET}")
    
    year_input = input(f"{Colors.GREEN}[+] Start Year (e.g. 2018, leave empty for all history): {Colors.RESET}").strip()
    start_year = year_input if year_input.isdigit() and len(year_input) == 4 else None

    print(f"\n{Colors.YELLOW}[*] Discovering full historical site tree for {domain} via CDX Global Index...{Colors.RESET}")
    discovered_paths = discover_historical_site_tree(domain)
    
    paths_by_cat = {
        "Contacts, Team & About (IT/EN)": [],
        "Partners & Clients (IT/EN)": [],
        "Products, Services & Projects (IT/EN)": []
    }
    
    if discovered_paths:
        for p in discovered_paths:
            cat = classify_url_category(p)
            if cat in paths_by_cat:
                paths_by_cat[cat].append(p)
        
        total_classified = sum(len(v) for v in paths_by_cat.values())
        if total_classified > 0:
            print(f"{Colors.GREEN}[+] Historical Site Tree Discovered: {len(discovered_paths)} unique paths found ({total_classified} targeted for corporate intelligence).{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}[!] CDX Tree query returned {len(discovered_paths)} paths, but none matched category keywords. Using standard fallback paths...{Colors.RESET}")
            paths_by_cat = PATHS_BY_CATEGORY
    else:
        print(f"{Colors.YELLOW}[!] CDX Global Tree query returned no results. Using standard fallback paths...{Colors.RESET}")
        paths_by_cat = PATHS_BY_CATEGORY

    print(f"\n{Colors.YELLOW}[*] Sampling unique historical snapshots across targeted categories...{Colors.RESET}")
    all_snapshots_to_process = []
    for cat_name, paths in paths_by_cat.items():
        if not paths:
            continue
        print(f"{Colors.CYAN}  -> Category: {cat_name} ({len(paths)} target paths){Colors.RESET}")
        for path in paths[:25]:  # Process up to 25 paths per category to keep execution swift
            snaps = fetch_historical_snapshots(domain, path, limit_per_year=1, start_year=start_year)
            if snaps:
                print(f"     [+] {path:<28} : {len(snaps)} unique snapshots")
                for ts, orig, digest in snaps:
                    all_snapshots_to_process.append((ts, orig, path))
            time.sleep(0.2)  # Gentle rate limiting for CDX queries

    if not all_snapshots_to_process:
        print(f"\n{Colors.YELLOW}[!] No historical snapshots discovered for targeted paths on {domain}.{Colors.RESET}")
        return

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Total unique snapshots queued for content harvesting: {len(all_snapshots_to_process)}{Colors.RESET}")
    
    # Aggregated timelines
    timeline = {
        "emails": {},
        "phones": {},
        "piva": {},
        "analytics_ids": {},
        "partners_clients": {},
        "products_projects": {}
    }

    print(f"{Colors.YELLOW}[*] Harvesting & extracting entities across historical snapshots (this may take a minute)...{Colors.RESET}\n")
    
    for idx, (ts, orig, path) in enumerate(all_snapshots_to_process, 1):
        fmt_date = format_timestamp(ts)
        print(f"\r{Colors.CYAN}[{idx}/{len(all_snapshots_to_process)}]{Colors.RESET} Harvesting {Colors.WHITE}{path:<20}{Colors.RESET} ({fmt_date})...", end="", flush=True)
        data = harvest_snapshot_data(ts, orig)
        if data:
            snap_link = f"https://web.archive.org/web/{ts}/{orig}"
            update_timeline(timeline["emails"], data["emails"], fmt_date, snap_link)
            update_timeline(timeline["phones"], data["phones"], fmt_date, snap_link)
            update_timeline(timeline["piva"], data["piva"], fmt_date, snap_link)
            update_timeline(timeline["analytics_ids"], data["analytics_ids"], fmt_date, snap_link)
            update_timeline(timeline["partners_clients"], data["partners_clients"], fmt_date, snap_link)
            update_timeline(timeline["products_projects"], data["products_projects"], fmt_date, snap_link)
        time.sleep(0.5)  # Respect Internet Archive servers

    print(f"\n\n{Colors.GREEN}{Colors.BOLD}=============================================================================")
    print(f"                 CORPORATE INTELLIGENCE & TIMELINE SUMMARY FOR {domain.upper()}")
    print("=============================================================================" + Colors.RESET)

    for category, items in timeline.items():
        title = category.replace('_', ' ').upper()
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}[-- {title} ({len(items)} found) --]{Colors.RESET}")
        if not items:
            print(f"  {Colors.WHITE}None discovered.{Colors.RESET}")
            continue
        for name, meta in sorted(items.items(), key=lambda x: x[1]["first_seen"]):
            paths_str = ", ".join(sorted(meta["paths"]))
            period = f"{meta['first_seen']} -> {meta['last_seen']}" if meta['first_seen'] != meta['last_seen'] else f"{meta['first_seen']}"
            print(f"  {Colors.CYAN}[{period:<22}]{Colors.RESET} {Colors.WHITE}{name:<38}{Colors.RESET} {Colors.YELLOW}(Snapshot: {paths_str}){Colors.RESET}")

    # Prompt to save results
    save_opt = input(f"\n{Colors.GREEN}[+] Save Deep Intelligence report to JSON & TXT files? (y/N): {Colors.RESET}").strip().lower()
    if save_opt.startswith('y'):
        ts_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"wayback_intelligence_{domain}_{ts_str}.json"
        txt_file = f"wayback_intelligence_{domain}_{ts_str}.txt"
        
        # Serialize sets to lists for JSON
        json_timeline = {}
        for cat, items in timeline.items():
            json_timeline[cat] = {
                name: {
                    "first_seen": meta["first_seen"],
                    "last_seen": meta["last_seen"],
                    "snapshot_urls": sorted(list(meta["paths"]))
                } for name, meta in items.items()
            }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({"domain": domain, "timestamp": ts_str, "timeline": json_timeline}, f, indent=2, ensure_ascii=False)
            
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"WAYBACK MACHINE CORPORATE INTELLIGENCE REPORT FOR: {domain}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            for cat, items in timeline.items():
                f.write(f"=== {cat.replace('_', ' ').upper()} ({len(items)}) ===\n")
                for name, meta in sorted(items.items(), key=lambda x: x[1]["first_seen"]):
                    paths_str = ", ".join(sorted(meta["paths"]))
                    period = f"{meta['first_seen']} -> {meta['last_seen']}" if meta['first_seen'] != meta['last_seen'] else f"{meta['first_seen']}"
                    f.write(f"[{period}] {name} (Snapshot: {paths_str})\n")
                f.write("\n")

        print(f"{Colors.GREEN}[+] Reports saved successfully to:\n    - {json_file}\n    - {txt_file}{Colors.RESET}")


def run_wayback_recon():
    """Main entry point for Wayback Machine Reconnaissance."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("                 WAYBACK MACHINE HISTORICAL ARCHIVE RECON                    ")
    print("=============================================================================" + Colors.RESET)
    print(f"  {Colors.CYAN}[1]{Colors.RESET} Wayback CDX Interactive Dork Builder {Colors.YELLOW}(inurl, filetype, status, intext...){Colors.RESET}")
    print(f"  {Colors.CYAN}[2]{Colors.RESET} Deep Content & Corporate Intelligence Harvesting {Colors.YELLOW}(Team, Partners, Products){Colors.RESET}")
    print(f"  {Colors.CYAN}[0]{Colors.RESET} Return to Main Menu")

    choice = input(f"\n{Colors.GREEN}[+] Select Option (0-2): {Colors.RESET}").strip()
    if choice == "0":
        return
    
    domain = input(f"\n{Colors.GREEN}[+] Target Domain (e.g. example.com): {Colors.RESET}").strip()
    if not domain:
        return
    domain = clean_domain(domain)

    if choice == "1":
        run_wayback_cdx_dork_builder(domain)
    elif choice == "2":
        run_wayback_deep_harvesting(domain)
    else:
        print(f"{Colors.RED}[!] Invalid option selected.{Colors.RESET}")
