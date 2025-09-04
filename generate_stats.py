# generate_stats.py
import json
import os
import urllib.parse
import re

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
    # Replace spaces with underscore, strip bad characters
    name = (name or "Unknown").strip()
    # collapse whitespace to single underscore
    name = re.sub(r'\s+', '_', name)
    # remove filesystem-unfriendly chars
    name = re.sub(r'[^\w\-\.\+]', '_', name)
    if not name:
        name = "Unknown"
    return name

def main():
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: stats.json not found or is invalid. Skipping split process.")
        return

    by_protocol = {}
    by_country = {}

    for server in results or []:
        # Original URL (fallback-safe)
        original_url = get_nested_ci(server, ['Proxy', 'OriginalURL'], '') or ''
        original_url = original_url.strip()
        if not original_url:
            continue
        clean_url = original_url.split('#', 1)[0]

        # Extract blocks (case-insensitive)
        location = get_nested_ci(server, ['Location'], {}) or {}
        asn = get_nested_ci(server, ['ASN'], {}) or {}

        # Country code & name
        country_code = get_ci(location, 'countryCode') or get_ci(location, 'country_code') or ''
        country_name = get_ci(location, 'country') or 'Unknown'
        country_code = (country_code or '').strip().upper()
        # Choose grouping key for country: prefer valid 2-letter code, else name
        if re.fullmatch(r'[A-Z]{2}', country_code):
            country_key = country_code
        else:
            country_key = country_name.strip() or 'Unknown'

        # City (avoid adding 'Unknown')
        city = (get_ci(location, 'city') or '').strip()
        city_tag = f"-{city.replace(' ', '')}" if city and city.lower() != 'unknown' else ""

        # ISP (case-insensitive)
        isp = (get_ci(asn, 'isp') or 'Unknown').strip() or 'Unknown'

        # Latency as int with fallback
        latency_raw = server.get('Latency', 999)
        try:
            latency = int(latency_raw)
        except (TypeError, ValueError):
            latency = 999

        # Emoji from country code (only if valid)
        emoji = country_code_to_emoji(country_code)

        # Build tag and final URL
        tag_content = f"https://t.me/ForceRunVPN-{emoji}{city_tag}-{latency}ms-{isp}"
        final_url = f"{clean_url}#{urllib.parse.quote(tag_content, safe='')}"

        # Protocol (case-insensitive)
        protocol = (get_nested_ci(server, ['Proxy', 'Protocol'], 'unknown') or 'unknown').strip().lower()

        # Groupings (use sets to avoid duplicates)
        by_protocol.setdefault(protocol, set()).add(final_url)
        by_country.setdefault(country_key, set()).add(final_url)

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

if __name__ == "__main__":
    main()
