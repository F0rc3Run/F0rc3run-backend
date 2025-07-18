from flask import Flask, request, jsonify
import subprocess, json, os, time, base64

app = Flask(__name__)

@app.route('/')
def home():
    return {"message": "🚀 F0rc3Run API is online."}

@app.route('/test', methods=['POST'])
def test_vmess():
    data = request.get_json()
    if not data or "link" not in data:
        return jsonify({"error": "No link provided"}), 400

    link = data["link"]
    if not link.startswith("vmess://"):
        return jsonify({"error": "Only vmess supported"}), 400

    try:
        config = make_xray_config(link)

        with open("config.json", "w") as f:
            json.dump(config, f)

        # Run Xray
        print("🔧 Starting xray-core...")
        proc = subprocess.Popen(["./xray", "-config", "config.json"])
        time.sleep(3)

        start = time.time()
        result = subprocess.run([
            "curl", "--socks5", "127.0.0.1:10808", "-m", "6",
            "-s", "-o", "/dev/null", "https://www.google.com"
        ])
        end = time.time()

        proc.terminate()

        if result.returncode == 0:
            return jsonify({"success": True, "latency": int((end - start) * 1000)})
        else:
            return jsonify({"success": False, "error": "Connection failed"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def make_xray_config(link):
    decoded = base64.b64decode(link.replace('vmess://', '') + '===').decode()
    node = json.loads(decoded)

    return {
        "inbounds": [{
            "port": 10808,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": { "auth": "no_auth" }
        }],
        "outbounds": [{
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": node["add"],
                    "port": int(node["port"]),
                    "users": [{
                        "id": node["id"],
                        "alterId": int(node.get("aid", 0)),
                        "security": node.get("scy", "auto")
                    }]
                }]
            },
            "streamSettings": {
                "network": node.get("net", "tcp"),
                "security": node.get("tls", ""),
                "wsSettings": {
                    "path": node.get("path", ""),
                    "headers": {
                        "Host": node.get("host", "")
                    }
                } if node.get("net") == "ws" else {}
            }
        }]
    }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
