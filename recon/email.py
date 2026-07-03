# -*- coding: utf-8 -*-
"""
Email address OSINT & breach footprinting module.
"""

try:
    import dns.resolver  # type: ignore
except ImportError:
    dns = None

from core.config import Colors


def run_email_osint():
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("                   EMAIL ADDRESS OSINT & BREACH FOOTPRINTING                 ")
    print("=============================================================================" + Colors.RESET)
    
    email_input = input(f"{Colors.GREEN}[+] Enter Target Email Address (e.g. target@company.com): {Colors.RESET}").strip()
    if not email_input or '@' not in email_input:
        print(f"{Colors.RED}[!] Invalid email syntax provided.{Colors.RESET}")
        return None

    username, domain = email_input.split('@', 1)
    domain = domain.lower().strip()
    
    print(f"\n{Colors.YELLOW}[*] Performing offline analysis & DNS MX probe for {domain}...{Colors.RESET}")
    
    provider_type = "Custom / Self-Hosted Mail Server"
    mx_records = []
    
    free_providers = ["gmail.com", "yahoo.com", "yahoo.it", "hotmail.com", "hotmail.it", "outlook.com", "outlook.it", "live.com", "live.it", "icloud.com", "aol.com", "libero.it", "virgilio.it", "tiscali.it", "aruba.it", "fastwebnet.it", "alice.it", "tin.it"]
    privacy_providers = ["protonmail.com", "proton.me", "tutanota.com", "tuta.com", "tuta.io", "posteo.de", "mailbox.org"]
    
    if domain in free_providers:
        provider_type = "Public Free Webmail Provider"
    elif domain in privacy_providers:
        provider_type = "Encrypted / Privacy Webmail Provider"
    
    if dns is not None:
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            for rdata in sorted(answers, key=lambda x: x.preference):
                mx_host = str(rdata.exchange).rstrip('.')
                mx_records.append(f"{mx_host} (Pref: {rdata.preference})")
                mx_lower = mx_host.lower()
                if provider_type == "Custom / Self-Hosted Mail Server":
                    if "google.com" in mx_lower or "googlemail.com" in mx_lower:
                        provider_type = "Google Workspace (Corporate / Enterprise)"
                    elif "outlook.com" in mx_lower or "protection.outlook.com" in mx_lower:
                        provider_type = "Microsoft 365 / Exchange Corporate"
                    elif "zoho." in mx_lower:
                        provider_type = "Zoho Mail Corporate"
        except Exception:
            mx_records.append("MX lookup failed / No MX records found")
    else:
        mx_records.append("dnspython not installed (Skipping MX lookup)")

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Email Intelligence Summary:{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Target Email':<22}:{Colors.RESET} {Colors.WHITE}{email_input}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'User Handle':<22}:{Colors.RESET} {Colors.WHITE}{username}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Domain Name':<22}:{Colors.RESET} {Colors.WHITE}{domain}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Infrastructure Type':<22}:{Colors.RESET} {Colors.MAGENTA}{provider_type}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'MX Mail Exchange':<22}:{Colors.RESET} {Colors.WHITE}{', '.join(mx_records[:3]) if mx_records else 'None'}{Colors.RESET}")

    dorks = {
        "Exact Email Mentions": f'"{email_input}"',
        "Public Breach & Spreadsheet Leaks": f'("{email_input}") (filetype:xls OR filetype:xlsx OR filetype:csv OR filetype:sql OR filetype:txt OR filetype:json)',
        "Pastebin & Text Dump Search": f'("{email_input}") (site:pastebin.com OR site:justpaste.it OR site:rentry.co OR site:ghostbin.com)',
        "Professional & Developer Activity": f'("{email_input}" OR "{username}") (site:linkedin.com OR site:github.com OR site:gitlab.com OR site:stackoverflow.com)'
    }

    print(f"\n{Colors.CYAN}{Colors.BOLD}[+] Generated Email Footprint Dorks:{Colors.RESET}")
    dork_list = list(dorks.items())
    for idx, (title, q) in enumerate(dork_list, 1):
        print(f"  {Colors.YELLOW}[{idx}] {title}:{Colors.RESET}")
        print(f"      {Colors.WHITE}{q}{Colors.RESET}")

    print(f"\n{Colors.GREEN}[+] Select a footprint query to launch multi-engine scan immediately (1-{len(dork_list)}, or Enter to return): {Colors.RESET}", end="")
    scan_choice = input().strip()
    if scan_choice.isdigit() and 1 <= int(scan_choice) <= len(dork_list):
        return dork_list[int(scan_choice)-1][1]
    return None
