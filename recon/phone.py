# -*- coding: utf-8 -*-
"""
Phone number OSINT validation and footprint dork generator.
"""

import re

try:
    import phonenumbers  # type: ignore
    from phonenumbers import geocoder, carrier, timezone  # type: ignore
except ImportError:
    phonenumbers = None

from core.config import Colors


def run_phone_osint():
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Phone Number OSINT & Footprinting Suite ---{Colors.RESET}")
    number_str = input(f"{Colors.GREEN}[+] Target Phone Number (e.g. +39 340 1234567 or 02 1234567): {Colors.RESET}").strip()
    if not number_str:
        return None

    region_code = None
    if not number_str.startswith('+'):
        region_input = input(f"{Colors.GREEN}[+] Default Country Code for national format (e.g. IT, US, FR - press Enter for IT): {Colors.RESET}").strip().upper()
        region_code = region_input if region_input else "IT"

    print(f"\n{Colors.YELLOW}[*] Executing phone intelligence analysis...{Colors.RESET}")

    e164 = number_str
    national = number_str
    intl = number_str
    location = "Unknown"
    carrier_name = "Unknown"
    line_type = "Unknown / General"
    timezones = []
    is_valid = False

    if phonenumbers is not None:
        try:
            parsed = phonenumbers.parse(number_str, region_code)
            is_valid = phonenumbers.is_valid_number(parsed)
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            
            loc_desc = geocoder.description_for_number(parsed, "en")
            if loc_desc:
                location = loc_desc
            c_desc = carrier.name_for_number(parsed, "en")
            if c_desc:
                carrier_name = c_desc
            tz_list = timezone.time_zones_for_number(parsed)
            if tz_list and tz_list != ('Etc/Unknown',):
                timezones = list(tz_list)
            
            num_type = phonenumbers.number_type(parsed)
            type_map = {
                0: "Fixed Line", 1: "Mobile", 2: "Fixed Line OR Mobile",
                3: "Toll Free", 4: "Premium Rate", 5: "Shared Cost",
                6: "VoIP", 7: "Personal Number", 8: "Pager",
                9: "UAN", 10: "Voicemail"
            }
            line_type = type_map.get(num_type, "Unknown")
        except Exception:
            pass

    clean_digits = re.sub(r'\D', '', number_str)
    if not e164.startswith('+'):
        if region_code == "IT" and not clean_digits.startswith('39'):
            e164 = "+39" + clean_digits
            clean_digits = "39" + clean_digits
        elif clean_digits:
            e164 = "+" + clean_digits
    else:
        clean_digits = re.sub(r'\D', '', e164)

    if national == number_str and len(clean_digits) > 4:
        national = clean_digits[2:] if clean_digits.startswith('39') else clean_digits
    if intl == number_str and e164.startswith('+'):
        intl = e164

    # Built-in Deep Prefix & Carrier Intelligence Engine (Offline / Zero External Cost)
    cc_map = {
        "39": "Italy", "1": "USA / Canada (NANP)", "44": "United Kingdom", "33": "France",
        "49": "Germany", "34": "Spain", "41": "Switzerland", "43": "Austria", "31": "Netherlands",
        "32": "Belgium", "351": "Portugal", "30": "Greece", "46": "Sweden", "47": "Norway",
        "45": "Denmark", "358": "Finland", "48": "Poland", "420": "Czech Republic",
        "36": "Hungary", "40": "Romania", "380": "Ukraine", "7": "Russia / Kazakhstan",
        "86": "China", "81": "Japan", "82": "South Korea", "91": "India", "61": "Australia",
        "55": "Brazil", "52": "Mexico", "54": "Argentina", "27": "South Africa", "971": "UAE"
    }

    it_cities = {
        "06": "Roma (Lazio)", "02": "Milano (Lombardia)", "011": "Torino (Piemonte)",
        "081": "Napoli (Campania)", "055": "Firenze (Toscana)", "051": "Bologna (Emilia-Romagna)",
        "010": "Genova (Liguria)", "091": "Palermo (Sicilia)", "041": "Venezia (Veneto)",
        "080": "Bari (Puglia)", "095": "Catania (Sicilia)", "045": "Verona (Veneto)",
        "049": "Padova (Veneto)", "040": "Trieste (Friuli-Venezia Giulia)", "030": "Brescia (Lombardia)",
        "035": "Bergamo (Lombardia)", "0521": "Parma (Emilia-Romagna)", "059": "Modena (Emilia-Romagna)",
        "071": "Ancona (Marche)", "050": "Pisa (Toscana)", "075": "Perugia (Umbria)",
        "070": "Cagliari (Sardegna)", "090": "Messina (Sicilia)", "089": "Salerno (Campania)",
        "0541": "Rimini (Emilia-Romagna)", "0187": "La Spezia (Liguria)", "031": "Como (Lombardia)",
        "039": "Monza (Lombardia)", "0331": "Busto Arsizio / Varese (Lombardia)", "0862": "L'Aquila (Abruzzo)"
    }

    it_mobiles = {
        ("320", "327", "328", "329", "380", "388", "389", "390", "391", "392", "393"): "Wind Tre",
        ("330", "331", "333", "334", "335", "336", "337", "338", "339", "360", "366", "368"): "TIM (Telecom Italia Mobile)",
        ("340", "342", "345", "346", "347", "348", "349"): "Vodafone Italia",
        ("351", "352"): "Iliad Italia",
        ("370",): "TIM / MVNO (CoopVoce/Tiscali)",
        ("371",): "PosteMobile / Very Mobile",
        ("377",): "PosteMobile",
        ("378",): "Kena Mobile (MVNO TIM)",
        ("379",): "Fastweb / Eolo Mobile",
        ("350",): "Kena Mobile / MVNO"
    }

    if clean_digits.startswith("39") and len(clean_digits) > 4:
        local_part = clean_digits[2:]
        if location in ("Unknown", "Italy", ""):
            location = "Italy"
            if local_part.startswith("0"):
                line_type = "Fixed Line" if line_type in ("Unknown / General", "Unknown") else line_type
                for pfx, city in sorted(it_cities.items(), key=lambda x: len(x[0]), reverse=True):
                    if local_part.startswith(pfx):
                        location = f"Italy, {city}"
                        break
        if carrier_name in ("Unknown", "") and local_part.startswith("3"):
            line_type = "Mobile" if line_type in ("Unknown / General", "Unknown") else line_type
            pfx3 = local_part[:3]
            for pfx_tuple, c_name in it_mobiles.items():
                if pfx3 in pfx_tuple:
                    carrier_name = c_name
                    break
        if local_part.startswith("800"):
            line_type = "Toll Free (Numero Verde)"
            location = "Italy (National Toll Free)"
        elif local_part.startswith("899") or local_part.startswith("892"):
            line_type = "Premium Rate (Servizio a Sovrapprezzo)"
            location = "Italy (Special Rate)"
        if not timezones:
            timezones = ["Europe/Rome"]
        is_valid = True if len(local_part) in (9, 10, 11) else is_valid
    else:
        if location in ("Unknown", ""):
            for cc, c_name in sorted(cc_map.items(), key=lambda x: len(x[0]), reverse=True):
                if clean_digits.startswith(cc):
                    location = c_name
                    break

    print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Phone Intelligence Summary:{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Validity':<22}:{Colors.RESET} {Colors.GREEN if is_valid else Colors.YELLOW}{'Valid Number' if is_valid else 'Possible/Unverified Format'}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'E.164 Format':<22}:{Colors.RESET} {Colors.WHITE}{e164}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Intl Format':<22}:{Colors.RESET} {Colors.WHITE}{intl}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'National Format':<22}:{Colors.RESET} {Colors.WHITE}{national}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Location / Region':<22}:{Colors.RESET} {Colors.WHITE}{location}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Carrier Operator':<22}:{Colors.RESET} {Colors.WHITE}{carrier_name}{Colors.RESET}")
    print(f"  {Colors.CYAN}{'Line Type':<22}:{Colors.RESET} {Colors.WHITE}{line_type}{Colors.RESET}")
    if timezones:
        print(f"  {Colors.CYAN}{'Timezone(s)':<22}:{Colors.RESET} {Colors.WHITE}{', '.join(timezones)}{Colors.RESET}")
    if "Mobile" in line_type or clean_digits.startswith("393"):
        print(f"  {Colors.CYAN}{'MNP Portability Note':<22}:{Colors.RESET} {Colors.YELLOW}Carrier indicates original ministerial block allocation (subject to MNP portability){Colors.RESET}")

    clean_num = re.sub(r'\D', '', e164)
    dorks = {
        "General Web Footprint": f'"{e164}" OR "{intl}" OR "{national}"',
        "Messaging & Social": f'("{e164}" OR "{clean_num}") (site:t.me OR site:wa.me OR site:facebook.com OR site:linkedin.com)',
        "Reputation & Spam Directories": f'("{e164}" OR "{clean_num}") (truecaller OR tellows OR sync.me OR "who called" OR spam OR truffa)',
        "Document & Paste Leak Search": f'("{e164}" OR "{clean_num}") (filetype:pdf OR filetype:txt OR site:pastebin.com)'
    }

    print(f"\n{Colors.CYAN}{Colors.BOLD}[+] Generated Phone Footprint Dorks:{Colors.RESET}")
    dork_list = list(dorks.items())
    for idx, (title, q) in enumerate(dork_list, 1):
        print(f"  {Colors.YELLOW}[{idx}] {title}:{Colors.RESET}")
        print(f"      {Colors.WHITE}{q}{Colors.RESET}")

    print(f"\n{Colors.GREEN}[+] Select a footprint query to launch multi-engine scan immediately (1-{len(dork_list)}, or Enter to return): {Colors.RESET}", end="")
    scan_choice = input().strip()
    if scan_choice.isdigit() and 1 <= int(scan_choice) <= len(dork_list):
        return dork_list[int(scan_choice)-1][1]
    return None
