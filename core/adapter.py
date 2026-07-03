# -*- coding: utf-8 -*-
"""
Dork syntax adapter for converting queries across multiple search engines.
"""

import re


class DorkAdapter:
    """
    Translates canonical/Google-style dork queries into engine-specific syntax.
    """
    @staticmethod
    def adapt(query, engine):
        engine = engine.lower()
        adapted = query

        if engine in ["duckduckgo", "bing"]:
            # Bing/DDG support inbody: instead of intext: / allintext:
            adapted = re.sub(r'\ballintext:', 'inbody:', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\bintext:', 'inbody:', adapted, flags=re.IGNORECASE)
            # Replace allintitle: / allinurl: with intitle: / inurl:
            adapted = re.sub(r'\ballintitle:', 'intitle:', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\ballinurl:', 'inurl:', adapted, flags=re.IGNORECASE)

        elif engine == "yandex":
            # Yandex uses mime: instead of filetype: / ext:
            adapted = re.sub(r'\b(?:filetype|ext):([a-zA-Z0-9_-]+)', r'mime:\1', adapted, flags=re.IGNORECASE)
            # Yandex uses title: instead of intitle: / allintitle:
            adapted = re.sub(r'\b(?:intitle|allintitle):', 'title:', adapted, flags=re.IGNORECASE)
            # Yandex uses url: instead of inurl: / allinurl:
            adapted = re.sub(r'\b(?:inurl|allinurl):', 'url:', adapted, flags=re.IGNORECASE)
            # Yandex doesn't support intext: operator directly; convert to plain string search
            adapted = re.sub(r'\b(?:intext|allintext):("[^"]+"|\S+)', r'\1', adapted, flags=re.IGNORECASE)

        elif engine == "brave":
            # Brave Search supports site:, filetype:, intitle:, inurl:.
            # Convert unsupported intext:/allintext: to keywords
            adapted = re.sub(r'\b(?:intext|allintext|inbody):("[^"]+"|\S+)', r'\1', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\b(?:allintitle):', 'intitle:', adapted, flags=re.IGNORECASE)
            adapted = re.sub(r'\b(?:allinurl):', 'inurl:', adapted, flags=re.IGNORECASE)

        # Google supports canonical dorks naturally
        return adapted
