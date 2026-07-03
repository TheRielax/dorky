# -*- coding: utf-8 -*-
"""
Search engine adapters and execution engine.
"""

import time
import random
import urllib.parse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    pass

try:
    from ddgs import DDGS  # type: ignore
except ImportError:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        DDGS = None

try:
    from googlesearch import search as google_search  # type: ignore
except ImportError:
    google_search = None

from core.config import Colors, ConfigManager, get_random_headers


class SearchEngines:
    """
    Executes search queries against multiple engines using APIs or web scraping fallbacks.
    """
    @staticmethod
    def is_valid_url(url):
        if not url or not isinstance(url, str):
            return False
        url_str = url.strip()
        if not (url_str.startswith("http://") or url_str.startswith("https://")):
            return False
        invalid_sub = [
            "/clev?", "StartpageResultClick", "payload=",
            "google.com/url?", "bing.com/aclick", "yandex.ru/clck",
            "startpage.com/clev", "brave.com/", "duckduckgo.com/y.js"
        ]
        for sub in invalid_sub:
            if sub in url_str:
                return False
        return True

    @staticmethod
    def search_duckduckgo(query, max_results):
        results = []
        if DDGS is None:
            print(f"{Colors.RED}[!] DuckDuckGo error: 'ddgs' library not installed.{Colors.RESET}")
            return results
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                        results.append(r['href'])
        except Exception as e:
            if "No results found" not in str(e):
                print(f"{Colors.RED}[!] DuckDuckGo search failed: {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_bing(query, max_results):
        results = []
        if DDGS is None:
            print(f"{Colors.RED}[!] Bing error: 'ddgs' library not installed.{Colors.RESET}")
            return results
        for b_end in ["bing", None, "lite"]:
            try:
                with DDGS() as ddgs:
                    res_iter = ddgs.text(query, backend=b_end, max_results=max_results) if b_end else ddgs.text(query, max_results=max_results)
                    for r in res_iter:
                        if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                            results.append(r['href'])
                if results:
                    return results
            except Exception:
                time.sleep(random.uniform(0.3, 0.6))
                continue
        return results

    @staticmethod
    def search_google(query, max_results):
        results = []
        cfg = ConfigManager.load_config()
        g_key = cfg.get("google_api_key", "").strip()
        g_cse = cfg.get("google_cse_id", "").strip()
        if g_key and g_cse:
            try:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://www.googleapis.com/customsearch/v1?q={encoded}&key={g_key}&cx={g_cse}&num={min(max_results, 10)}"
                headers = {'Accept-Encoding': 'gzip, deflate'}
                resp = requests.get(url, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        link = item.get("link")
                        if link and SearchEngines.is_valid_url(link) and link not in results:
                            results.append(link)
                    if results:
                        return results
                else:
                    print(f"{Colors.YELLOW}[!] Google Custom Search API returned HTTP {resp.status_code}. Falling back to scraping...{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Google API request failed: {e}. Falling back to scraping...{Colors.RESET}")

        if DDGS is not None:
            for b_end in ["google", "bing", None, "lite"]:
                try:
                    with DDGS() as ddgs:
                        res_iter = ddgs.text(query, backend=b_end, max_results=max_results) if b_end else ddgs.text(query, max_results=max_results)
                        for r in res_iter:
                            if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                                results.append(r['href'])
                    if results:
                        return results
                except Exception:
                    time.sleep(random.uniform(0.3, 0.6))
                    continue

        if google_search is None:
            if not results:
                print(f"{Colors.RED}[!] Google error: 'googlesearch-python' library not installed.{Colors.RESET}")
            return results
        try:
            count = 0
            for url in google_search(query, num_results=max_results):
                if SearchEngines.is_valid_url(url) and url not in results:
                    results.append(url)
                    count += 1
                    if count >= max_results:
                        break
                    time.sleep(0.5)
        except Exception as e:
            if not results:
                print(f"{Colors.RED}[!] Google search failed (possibly rate-limited): {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_brave(query, max_results):
        results = []
        cfg = ConfigManager.load_config()
        b_key = cfg.get("brave_api_key", "").strip()
        if b_key:
            try:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={min(max_results, 20)}"
                headers = {"Accept": "application/json", "Accept-Encoding": "gzip, deflate", "X-Subscription-Token": b_key}
                resp = requests.get(url, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    web_res = data.get("web", {}).get("results", [])
                    for item in web_res:
                        u = item.get("url")
                        if u and SearchEngines.is_valid_url(u) and u not in results:
                            results.append(u)
                    if results:
                        return results
                else:
                    print(f"{Colors.YELLOW}[!] Brave API returned HTTP {resp.status_code}. Falling back to scraping...{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Brave API failed: {e}. Falling back to scraping...{Colors.RESET}")

        if DDGS is not None:
            for b_end in ["brave", "bing", None, "lite"]:
                try:
                    with DDGS() as ddgs:
                        res_iter = ddgs.text(query, backend=b_end, max_results=max_results) if b_end else ddgs.text(query, max_results=max_results)
                        for r in res_iter:
                            if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                                results.append(r['href'])
                    if results:
                        return results
                except Exception:
                    time.sleep(random.uniform(0.3, 0.6))
                    continue

        headers = get_random_headers()
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://search.brave.com/search?q={encoded_query}"
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if SearchEngines.is_valid_url(href) and 'brave.com' not in href and href not in results:
                        results.append(href)
                        if len(results) >= max_results:
                            break
            else:
                if not results:
                    print(f"{Colors.YELLOW}[!] Brave returned HTTP {response.status_code} (Rate-limited).{Colors.RESET}")
        except Exception as e:
            if not results:
                print(f"{Colors.RED}[!] Brave search failed: {e}{Colors.RESET}")
        return results

    @staticmethod
    def search_yandex(query, max_results):
        results = []
        if DDGS is not None:
            for b_end in ["yandex", "bing", None, "lite"]:
                try:
                    with DDGS() as ddgs:
                        res_iter = ddgs.text(query, backend=b_end, max_results=max_results) if b_end else ddgs.text(query, max_results=max_results)
                        for r in res_iter:
                            if 'href' in r and SearchEngines.is_valid_url(r['href']) and r['href'] not in results:
                                results.append(r['href'])
                    if results:
                        return results
                except Exception:
                    time.sleep(random.uniform(0.3, 0.6))
                    continue

        headers = get_random_headers()
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://yandex.com/search/?text={encoded_query}"
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_str = soup.title.string.lower() if soup.title and soup.title.string else ""
                if 'verification' in title_str or 'captcha' in title_str:
                    if not results:
                        print(f"{Colors.YELLOW}[!] Yandex CAPTCHA verification triggered.{Colors.RESET}")
                else:
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        if SearchEngines.is_valid_url(href) and 'yandex.' not in href and 'yastatic.net' not in href and href not in results:
                            results.append(href)
                            if len(results) >= max_results:
                                break
            else:
                if not results:
                    print(f"{Colors.YELLOW}[!] Yandex returned HTTP {response.status_code}.{Colors.RESET}")
        except Exception as e:
            if not results:
                print(f"{Colors.RED}[!] Yandex search failed: {e}{Colors.RESET}")
        return results
