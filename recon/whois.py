# -*- coding: utf-8 -*-
"""
Passive DNS, WHOIS & Security Posture (SPF/DMARC) module.
"""

import re
import socket

try:
    import whois as pywhois  # type: ignore
except ImportError:
    pywhois = None

try:
    import dns.resolver  # type: ignore
except ImportError:
    dns = None

from core.config import Colors


def run_dns_whois_osint():
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("             PASSIVE DNS, WHOIS & SECURITY POSTURE (SPF/DMARC)               ")
    print("=============================================================================" + Colors.RESET)
    
    target = input(f"{Colors.GREEN}[+] Enter Target Domain Name (e.g. company.com): {Colors.RESET}").strip()
    if not target:
        return None
    target = re.sub(r'^https?://', '', target).split('/')[0].lower().strip()
    
    print(f"\n{Colors.YELLOW}[*] Executing WHOIS query & passive DNS infrastructure audit for {target}...{Colors.RESET}")
    
    registrar = "Unknown"
    creation_date = "Unknown"
    expiry_date = "Unknown"
    org = "Unknown / Privacy Protected"
    raw_text = ""
    w = None
    
    if pywhois is not None:
        try:
            w = pywhois.whois(target)
            if hasattr(w, 'text') and w.text:
                raw_text += str(w.text) + "\n"
        except Exception:
            pass

    if not raw_text or len(raw_text) < 100 or ("Organization:" not in raw_text and "Registrant" not in raw_text):
        try:
            import subprocess
            res = subprocess.run(["whois", target], capture_output=True, text=True, timeout=5)
            if res.stdout:
                raw_text += "\n" + res.stdout
        except Exception:
            pass

    if not raw_text or len(raw_text) < 100 or ("Organization:" not in raw_text and "Registrant" not in raw_text):
        try:
            tld = target.split('.')[-1]
            whois_server = f"whois.nic.{tld}" if tld in ['it', 'uk', 'fr', 'de', 'nl', 'eu'] else "whois.verisign-grs.com"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((whois_server, 43))
            s.send(f"{target}\r\n".encode('utf-8'))
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            s.close()
            raw_text += "\n" + response.decode('utf-8', errors='ignore')
        except Exception:
            pass

    if w is not None:
        if w.registrar:
            registrar = str(w.registrar)
        if w.creation_date:
            c_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
            creation_date = str(c_date)[:10]
        if w.expiration_date:
            e_date = w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date
            expiry_date = str(e_date)[:10]
        if w.org:
            org = str(w.org)

    if org == "Unknown / Privacy Protected" or org == "None" or not org:
        reg_match = re.search(r'(?:Registrant|Admin Contact|Technical Contact)\s*[\r\n]+(?:\s+[^\r\n]+[\r\n]+)*?\s*(?:Organization|Org|Name|Holder):\s*([^\r\n]+)', raw_text, re.IGNORECASE)
        if reg_match and reg_match.group(1).strip() and "REDACTED" not in reg_match.group(1).upper():
            org = reg_match.group(1).strip()
        else:
            line_match = re.search(r'^\s*(?:Registrant Organization|Registrant Name|Holder|Org|Organization):\s*([^\r\n]+)', raw_text, re.IGNORECASE | re.MULTILINE)
            if line_match and line_match.group(1).strip() and "REDACTED" not in line_match.group(1).upper():
                org = line_match.group(1).strip()

    if registrar == "Unknown" or registrar == "None" or not registrar:
        reg_match = re.search(r'Registrar\s*[\r\n]+(?:\s+[^\r\n]+[\r\n]+)*?\s*(?:Organization|Name):\s*([^\r\n]+)', raw_text, re.IGNORECASE)
        if reg_match:
            registrar = reg_match.group(1).strip()
        else:
            line_match = re.search(r'^\s*Registrar:\s*([^\r\n]+)', raw_text, re.IGNORECASE | re.MULTILINE)
            if line_match:
                registrar = line_match.group(1).strip()

    if creation_date == "Unknown" or not creation_date:
        c_match = re.search(r'^\s*(?:Created|Creation Date):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', raw_text, re.IGNORECASE | re.MULTILINE)
        if c_match:
            creation_date = c_match.group(1).strip()

    if expiry_date == "Unknown" or not expiry_date:
        e_match = re.search(r'^\s*(?:Expire Date|Expiration Date|Registry Expiry Date):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', raw_text, re.IGNORECASE | re.MULTILINE)
        if e_match:
            expiry_date = e_match.group(1).strip()

    ipv4_addrs = []
    try:
        for info in socket.getaddrinfo(target, None, socket.AF_INET):
            addr = info[4][0]
            if addr not in ipv4_addrs:
                ipv4_addrs.append(addr)
    except Exception:
        ipv4_addrs.append("Unresolved")

    spf_policy = "Missing / Not Configured (Vulnerable to Spoofing!)"
    dmarc_policy = "Missing / Not Configured (Vulnerable to Spoofing!)"
    spf_color = Colors.RED
    dmarc_color = Colors.RED
    
    if dns is not None:
        try:
            txt_ans = dns.resolver.resolve(target, 'TXT')
            for rdata in txt_ans:
                txt_str = "".join([b.decode('utf-8', errors='ignore') for b in rdata.strings])
                if txt_str.startswith("v=spf1"):
                    spf_policy = txt_str
                    if "-all" in txt_str:
                        spf_color = Colors.GREEN
                    elif "~all" in txt_str:
                        spf_color = Colors.YELLOW
        except Exception:
            pass
            
        try:
            dmarc_ans = dns.resolver.resolve(f"_dmarc.{target}", 'TXT')
            for rdata in dmarc_ans:
                txt_str = "".join([b.decode('utf-8', errors='ignore') for b in rdata.strings])
                if txt_str.startswith("v=DMARC1"):
                    dmarc_policy = txt_str
                    if "p=reject" in txt_str:
                        dmarc_color = Colors.GREEN
                    elif "p=quarantine" in txt_str:
                        dmarc_color = Colors.YELLOW
        except Exception:
            pass

    def get_contact_lines(section_name, txt):
        m = re.search(rf'{section_name}s?[\r\n]+((?:\s+[^\r\n]+[\r\n]*)+)', txt, re.IGNORECASE)
        if not m:
            return []
        res = []
        for l in m.group(1).splitlines():
            l = l.strip()
            if not l or l.startswith("Created:") or l.startswith("Last Update:"):
                continue
            if ':' in l:
                parts = l.split(':', 1)
                res.append((parts[0].strip(), parts[1].strip()))
            else:
                res.append(("", l))
        return res

    reg_lines = get_contact_lines("Registrant", raw_text)
    admin_lines = get_contact_lines("Admin Contact", raw_text)
    tech_lines = get_contact_lines("Technical Contact", raw_text)

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] WHOIS Registrant Summary:{Colors.RESET}")
    if reg_lines:
        for k, v in reg_lines:
            if k:
                print(f"  {Colors.CYAN}{k:<22}:{Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}{'':<22} {Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
    else:
        print(f"  {Colors.CYAN}{'Organization':<22}:{Colors.RESET} {Colors.WHITE}{org}{Colors.RESET}")
        if w is not None and getattr(w, 'address', None):
            print(f"  {Colors.CYAN}{'Address':<22}:{Colors.RESET} {Colors.WHITE}{w.address}{Colors.RESET}")

    if admin_lines:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] WHOIS Administrative Contact:{Colors.RESET}")
        for k, v in admin_lines:
            if k:
                print(f"  {Colors.CYAN}{k:<22}:{Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}{'':<22} {Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
    elif w is not None and (getattr(w, 'admin_name', None) or getattr(w, 'admin_org', None)):
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] WHOIS Administrative Contact:{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Name':<22}:{Colors.RESET} {Colors.WHITE}{getattr(w, 'admin_name', 'Unknown')}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Organization':<22}:{Colors.RESET} {Colors.WHITE}{getattr(w, 'admin_org', 'Unknown')}{Colors.RESET}")

    if tech_lines:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] WHOIS Technical Contact:{Colors.RESET}")
        for k, v in tech_lines:
            if k:
                print(f"  {Colors.CYAN}{k:<22}:{Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
            else:
                print(f"  {Colors.CYAN}{'':<22} {Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
    elif w is not None and (getattr(w, 'tech_name', None) or getattr(w, 'tech_org', None)):
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] WHOIS Technical Contact:{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Name':<22}:{Colors.RESET} {Colors.WHITE}{getattr(w, 'tech_name', 'Unknown')}{Colors.RESET}")
        print(f"  {Colors.CYAN}{'Organization':<22}:{Colors.RESET} {Colors.WHITE}{getattr(w, 'tech_org', 'Unknown')}{Colors.RESET}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Registrar & DNS Infrastructure:{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Registrar Name':<22}:{Colors.RESET} {Colors.WHITE}{registrar}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Created / Expiry':<22}:{Colors.RESET} {Colors.WHITE}{creation_date} to {expiry_date}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Resolved IPv4':<22}:{Colors.RESET} {Colors.WHITE}{', '.join(ipv4_addrs[:4])}{Colors.RESET}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Email Spoofing Security Posture (Anti-Phishing Audit):{Colors.RESET}")
    print(f"  {Colors.CYAN}{'SPF Record':<22}:{Colors.RESET} {spf_color}{spf_policy}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'DMARC Record':<22}:{Colors.RESET} {dmarc_color}{dmarc_policy}{Colors.RESET}")

    if raw_text.strip():
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}=============================================================================")
        print("                        COMPLETE RAW WHOIS RECORD OUTPUT                     ")
        print("=============================================================================" + Colors.RESET)
        for rline in raw_text.strip().splitlines():
            print(f"  {Colors.WHITE}{rline}{Colors.RESET}")
        print(f"{Colors.MAGENTA}============================================================================={Colors.RESET}")

    dorks = {
        "Full Site Indexing & General Web Footprint": f'site:{target}',
        "Subdomain & Dev/Staging Discovery": f'site:{target} (inurl:dev OR inurl:test OR inurl:staging OR inurl:api OR inurl:portal OR inurl:app)',
        "Administrative & Login Panels": f'site:{target} (inurl:admin OR inurl:login OR inurl:portal OR intitle:"dashboard" OR intitle:"login")',
        "Exposed Configuration & Env Files": f'site:{target} (filetype:xml OR filetype:conf OR filetype:cfg OR filetype:env OR filetype:ini OR filetype:log)',
        "Public Document & Backup Harvester": f'site:{target} (filetype:pdf OR filetype:docx OR filetype:xlsx OR filetype:sql OR filetype:bkp OR filetype:db)'
    }

    print(f"\n{Colors.CYAN}{Colors.BOLD}[+] Generated Domain Infrastructure Dorks:{Colors.RESET}")
    dork_list = list(dorks.items())
    for idx, (title, q) in enumerate(dork_list, 1):
        print(f"  {Colors.YELLOW}[{idx}] {title}:{Colors.RESET}")
        print(f"      {Colors.WHITE}{q}{Colors.RESET}")

    print(f"\n{Colors.GREEN}[+] Select a footprint query to launch multi-engine scan immediately (1-{len(dork_list)}, or Enter to return): {Colors.RESET}", end="")
    scan_choice = input().strip()
    if scan_choice.isdigit() and 1 <= int(scan_choice) <= len(dork_list):
        return dork_list[int(scan_choice)-1][1]
    return None
