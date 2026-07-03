# -*- coding: utf-8 -*-
"""
Username & social cross-platform footprinting module.
"""

import random

try:
    import requests
except ImportError:
    pass

from core.config import Colors, USER_AGENTS


def run_username_osint():
    print(f"\n{Colors.CYAN}{Colors.BOLD}=============================================================================")
    print("                 USERNAME & SOCIAL CROSS-PLATFORM FOOTPRINTING               ")
    print("=============================================================================" + Colors.RESET)
    
    uname = input(f"{Colors.GREEN}[+] Enter Target Username / Handle: {Colors.RESET}").strip()
    if not uname:
        return None
        
    print(f"\n{Colors.YELLOW}[*] Probing public profile endpoints across platforms in real-time...{Colors.RESET}\n")
    
    platforms = [
        ("GitHub", f"https://github.com/{uname}"),
        ("Reddit", f"https://www.reddit.com/user/{uname}"),
        ("Telegram", f"https://t.me/{uname}"),
        ("Steam", f"https://steamcommunity.com/id/{uname}"),
        ("HackTheBox", f"https://app.hackthebox.com/users/{uname}"),
        ("Pinterest", f"https://www.pinterest.com/{uname}/"),
        ("Vimeo", f"https://vimeo.com/{uname}"),
        ("SoundCloud", f"https://soundcloud.com/{uname}"),
        ("GitLab", f"https://gitlab.com/{uname}"),
        ("Bitbucket", f"https://bitbucket.org/{uname}/"),
        ("Pastebin", f"https://pastebin.com/u/{uname}"),
        ("Spotify", f"https://open.spotify.com/user/{uname}"),
        ("Wikipedia", f"https://en.wikipedia.org/wiki/User:{uname}")
    ]
    
    found_urls = []
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    for name, url in platforms:
        try:
            resp = requests.get(url, headers=headers, timeout=4, allow_redirects=True)
            if resp.status_code == 200 and "Not Found" not in resp.text[:1000] and "Page not found" not in resp.text[:1000]:
                print(f"  {Colors.GREEN}{Colors.BOLD}[FOUND]{Colors.RESET}     {name:<12} : {Colors.WHITE}{url}{Colors.RESET}")
                found_urls.append((name, url))
            else:
                print(f"  {Colors.WHITE}[NOT FOUND]{Colors.RESET} {name:<12} : {Colors.WHITE}{url}{Colors.RESET}")
        except Exception:
            print(f"  {Colors.YELLOW}[TIMEOUT]{Colors.RESET}   {name:<12} : {Colors.WHITE}{url}{Colors.RESET}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Username Probe Summary: {len(found_urls)} active profiles confirmed out of {len(platforms)} checked.{Colors.RESET}")

    dorks = {
        "Cross-Platform Profile Hunt": f'("{uname}") (site:github.com OR site:reddit.com OR site:t.me OR site:linkedin.com OR site:twitter.com OR site:instagram.com)',
        "Code & Repository Mentions": f'("{uname}") (site:pastebin.com OR site:gitlab.com OR site:bitbucket.org OR site:sourceforge.net)',
        "Forum & Discussion Activity": f'intitle:"{uname}" OR inurl:"user/{uname}" OR inurl:"profile/{uname}" OR inurl:"member/{uname}"'
    }

    print(f"\n{Colors.CYAN}{Colors.BOLD}[+] Generated Username Footprint Dorks:{Colors.RESET}")
    dork_list = list(dorks.items())
    for idx, (title, q) in enumerate(dork_list, 1):
        print(f"  {Colors.YELLOW}[{idx}] {title}:{Colors.RESET}")
        print(f"      {Colors.WHITE}{q}{Colors.RESET}")

    print(f"\n{Colors.GREEN}[+] Select a footprint query to launch multi-engine scan immediately (1-{len(dork_list)}, or Enter to return): {Colors.RESET}", end="")
    scan_choice = input().strip()
    if scan_choice.isdigit() and 1 <= int(scan_choice) <= len(dork_list):
        return dork_list[int(scan_choice)-1][1]
    return None
