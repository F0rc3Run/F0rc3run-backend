# generate_stats.py
import json
import os
import urllib.parse
import re
from collections import Counter

def country_code_to_emoji(code):
    """Converts a two-letter country code (A-Z) to a flag emoji, else returns 🏁."""
    if not isinstance(code, str):
        return '🏁'
    code = code.strip().upper()
    if not re.fullmatch(r'[A-Z]{2}', code):
        return '🏁'
    return "".join(chr(ord(c) + 127397) for c in code)

def get_ci(d, key, default=None):
    """Case-insensitive dict get."""
    if not isinstance(d, dict):
        return default
    key_lower = key.lower()
    for k, v in d.items():
        if isinstance(k, str) and k.lower() == key_lower:
            return v
    return default

def get_nested_ci(d, keys, default=None):
    """Case-insensitive nested get: keys is a list like ['Location','countryCode']"""
    cur = d
    for k in keys:
        cur = get_ci(cur, k)
        if cur is None:
            return default
    return cur

def sanitize_filename(name: str) -> str:
    name = (name or "Unknown").strip()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^\w\-\.\+]', '_', name)
    return name or "Unknown"

def main():
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: stats.json not found or is invalid. Skipping split process.")
        return

    by_protocol = {}
    by_country = {}
    protocol_counter = Counter()
    country_counter = Counter()

    total_servers = 0
    alive_servers = 0

    for server in results or []:
        total_servers += 1
        if server.get('IsAlive'):
            alive_servers += 1

        # Original URL
        original_url = get_nested_ci(server, ['Proxy', 'OriginalURL'], '') or ''
        original_url = original_url.strip()
        if not original_url:
            continue
        clean_url = original_url.split('#', 1)[0]

        # Extract blocks
        location = get_nested_ci(server, ['Location'], {}) or {}
        asn = get_nested_ci(server, ['ASN'], {}) or {}

        country_code = get_ci(location, 'countryCode') or ''
        country_name = get_ci(location, 'country') or 'Unknown'
        country_code = (country_code or '').strip().upper()

        if re.fullmatch(r'[A-Z]{2}', country_code):
            country_key = country_code
        else:
            country_key = country_name.strip() or 'Unknown'

        city = (get_ci(location, 'city') or '').strip()
        city_tag = f"-{city.replace(' ', '')}" if city and city.lower() != 'unknown' else ""

        isp = (get_ci(asn, 'isp') or 'Unknown').strip() or 'Unknown'

        latency_raw = server.get('Latency', 999)
        try:
            latency = int(latency_raw)
        except (TypeError, ValueError):
            latency = 999

        emoji = country_code_to_emoji(country_code)
        tag_content = f"https://t.me/ForceRunVPN-{emoji}{city_tag}-{latency}ms-{isp}"
        final_url = f"{clean_url}#{urllib.parse.quote(tag_content, safe='')}"

        protocol = (get_nested_ci(server, ['Proxy', 'Protocol'], 'unknown') or 'unknown').strip().lower()

        by_protocol.setdefault(protocol, set()).add(final_url)
        by_country.setdefault(country_key, set()).add(final_url)

        protocol_counter[protocol] += 1
        country_counter[country_key] += 1

    # --- Write protocol files ---
    proto_dir = "splitted-by-protocol"
    os.makedirs(proto_dir, exist_ok=True)
    for protocol, urls in by_protocol.items():
        path = os.path.join(proto_dir, f"{sanitize_filename(protocol)}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(urls)))
    print(f"Successfully created {len(by_protocol)} protocol files.")

    # --- Write country files ---
    country_dir = "splitted-by-country"
    os.makedirs(country_dir, exist_ok=True)
    for country, urls in by_country.items():
        filename = sanitize_filename(country) + ".txt"
        with open(os.path.join(country_dir, filename), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(urls)))
    print(f"Successfully created {len(by_country)} country files.")

    # --- Write summary.md ---
    summary = {
        "total_servers": total_servers,
        "alive_servers": alive_servers,
        "protocols": dict(protocol_counter),
        "countries": dict(country_counter)
    }
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write("```json\n")
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n```")
    print("summary.md created.")

if __name__ == "__main__":
    main()
