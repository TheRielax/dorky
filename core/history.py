# -*- coding: utf-8 -*-
"""
History tracking and result export utilities (TXT, JSON, CSV).
"""

import os
import json
import csv
from datetime import datetime
from core.config import Colors


class HistoryManager:
    """
    Persistent session & search history tracking.
    """
    HISTORY_FILE = "history.json"

    @classmethod
    def log_search(cls, query, engine_results, target_domain=""):
        history = cls.load_history()
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "target_domain": target_domain,
            "engines": {}
        }
        for eng, data in engine_results.items():
            entry["engines"][eng] = {
                "adapted_query": data.get("adapted_query", ""),
                "results_count": len(data.get("urls", []))
            }
        history.insert(0, entry)
        history = history[:100]
        try:
            with open(cls.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4)
        except Exception:
            pass

    @classmethod
    def load_history(cls):
        if os.path.exists(cls.HISTORY_FILE):
            try:
                with open(cls.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        else:
            try:
                with open(cls.HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4)
            except Exception:
                pass
        return []

    @classmethod
    def view_and_rerun(cls):
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- Search History Sessions ---{Colors.RESET}")
        history = cls.load_history()
        if not history:
            print(f"{Colors.YELLOW}[!] No search history found.{Colors.RESET}")
            return None

        for idx, entry in enumerate(history[:15], 1):
            ts = entry.get("timestamp", "")
            q = entry.get("query", "")
            eng_summary = ", ".join([f"{k} ({v['results_count']})" for k, v in entry.get("engines", {}).items()])
            print(f"  {Colors.CYAN}[{idx}]{Colors.RESET} {ts} | {Colors.YELLOW}{q}{Colors.RESET} | Engines: {eng_summary}")

        print("  [0] Return to main menu")
        choice = input(f"\n{Colors.GREEN}[+] Select history entry to re-run (0-{min(len(history), 15)}): {Colors.RESET}").strip()
        try:
            val = int(choice)
            if 1 <= val <= len(history):
                return history[val - 1].get("query")
        except ValueError:
            pass
        return None


def save_results(results_data, base_filename, output_format):
    """Save collected search results to disk in TXT, JSON, or CSV format."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{base_filename}_{timestamp}.{output_format}"

    try:
        if output_format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=4)
        elif output_format == "csv":
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Engine", "Adapted Query", "Rank", "URL"])
                for engine, data in results_data.items():
                    query = data["adapted_query"]
                    for idx, url in enumerate(data["urls"], 1):
                        writer.writerow([engine, query, idx, url])
        else: # txt
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== DORKY SEARCH RESULTS ({timestamp}) ===\n\n")
                for engine, data in results_data.items():
                    f.write(f"--- Engine: {engine.upper()} ---\n")
                    f.write(f"Adapted Query: {data['adapted_query']}\n")
                    if data["urls"]:
                        for idx, url in enumerate(data["urls"], 1):
                            f.write(f"[{idx}] {url}\n")
                    else:
                        f.write("No results found.\n")
                    f.write("\n")
        print(f"{Colors.GREEN}{Colors.BOLD}[+] Results successfully saved to: {filename}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}[!] Failed to save results: {e}{Colors.RESET}")
