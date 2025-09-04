# generate_stats.py
import json
import os
import urllib.parse

def country_code_to_emoji(code):
    """Converts a two-letter country code to a flag emoji."""
    if not isinstance(code, str) or len(code) != 2:
        return '🏁'
    return "".join(chr(ord(char.upper()) + 127397) for char in code)

def main():
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: stats.json not found or is invalid. Skipping split process.")
        return

    # Create dictionaries to group servers
    by_protocol = {}
    by_country = {}

    # Group servers by protocol and country
    for server in results:
        # Reconstruct the final tagged URL
        original_url = server.get('Proxy', {}).get('OriginalURL', '')
        if not original_url:
            continue
        
        clean_url = original_url.split('#')[0]
        
        location = server.get('Location', {})
        asn = server.get('ASN', {})
        
        emoji = country_code_to_emoji(location.get('CountryCode'))
        city_tag = ""
        if location.get('City'):
            city_tag = "-" + location.get('City').replace(" ", "")
            
        tag_content = "https://t.me/ForceRunVPN-{}{}-{:d}ms-{}".format(
            emoji,
            city_tag,
            server.get('Latency', 999),
            asn.get('ISP', 'Unknown')
        )
        final_url = f"{clean_url}#{urllib.parse.quote(tag_content)}"

        # Group by protocol
        protocol = server.get('Proxy', {}).get('Protocol', 'unknown').lower()
        if protocol not in by_protocol:
            by_protocol[protocol] = []
        by_protocol[protocol].append(final_url)

        # Group by country
        country = location.get('Country', 'Unknown')
        if country not in by_country:
            by_country[country] = []
        by_country[country].append(final_url)

    # --- Write protocol files ---
    proto_dir = "splitted-by-protocol"
    os.makedirs(proto_dir, exist_ok=True)
    for protocol, urls in by_protocol.items():
        with open(os.path.join(proto_dir, f"{protocol}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(urls))
    print(f"Successfully created {len(by_protocol)} protocol files.")

    # --- Write country files ---
    country_dir = "splitted-by-country"
    os.makedirs(country_dir, exist_ok=True)
    for country, urls in by_country.items():
        # Sanitize country name for filename
        filename = country.replace(" ", "_") + ".txt"
        with open(os.path.join(country_dir, filename), "w", encoding="utf-8") as f:
            f.write("\n".join(urls))
    print(f"Successfully created {len(by_country)} country files.")

if __name__ == "__main__":
    main()
