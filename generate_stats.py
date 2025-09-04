import json
import re
from datetime import datetime, timezone

def country_code_to_emoji(code):
    if not isinstance(code, str) or len(code) != 2:
        return '🏁'
    return "".join(chr(ord(char.upper()) + 127397) for char in code)

def update_readme(stats_content):
    readme_path = "README.md"
    start_marker = ""
    end_marker = ""
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        if start_marker not in content or end_marker not in content:
            print("Error: Markers not found in README.md. Please add them.")
            return
        new_content = re.sub(
            f"{re.escape(start_marker)}.*{re.escape(end_marker)}",
            f"{start_marker}\n{stats_content}\n{end_marker}",
            content,
            flags=re.DOTALL
        )
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md updated successfully.")
    except FileNotFoundError:
        print("Error: README.md not found.")

def main():
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: stats.json not found or is invalid.")
        return

    servers_by_country = {}
    for r in results:
        country = r.get('Location', {}).get('Country', 'Unknown')
        if country == 'Unknown':
            continue
        if country not in servers_by_country:
            servers_by_country[country] = {
                'servers': [], 
                'code': r.get('Location', {}).get('CountryCode', '--')
            }
        servers_by_country[country]['servers'].append(r)

    md = []
    update_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S (UTC)")
    md.append(f"### 🎌 آخرین به‌روزرسانی: {update_time}")
    md.append(f"### ✨ تعداد کل سرورهای فعال: {len(results)}\n")

    sorted_countries = sorted(servers_by_country.items(), key=lambda item: len(item[1]['servers']), reverse=True)

    for country, data in sorted_countries:
        emoji = country_code_to_emoji(data['code'])
        protocols = {}
        for server in data['servers']:
            proto = server.get('Proxy', {}).get('Protocol', 'N/A').upper()
            protocols[proto] = protocols.get(proto, 0) + 1
        protocol_counts = ", ".join([f"{p} ({c})" for p, c in sorted(protocols.items())])
        md.append(f"#### {emoji} {country}")
        md.append(f"**{len(data['servers'])} Server | Protocols: {protocol_counts}**\n")

    md_content = "\n".join(md)
    update_readme(md_content)

    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("summary.md created successfully.")

if __name__ == "__main__":
    main()
