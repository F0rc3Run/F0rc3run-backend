from flask import Flask, request, jsonify
import subprocess, json, os, time, base64

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "F0rc3Run URL Test API Online"}

@app.route('/test', methods=['POST'])
def test_proxy():
    data = request.get_json()
    link = data.get("link")

    if not link.startswith("vmess://"):
        return {"error": "Only vmess:// supported"}, 400

    try:
        vmess_config = parse_vmess(link)
        xray_config = generate_xray_config(vmess_config)

        with open("xray_config.json", "w") as f:
            json.dump(xray_config, f)

        xray_proc = subprocess.Popen(["./xray/xray", "-config", "xray_config.json"])
        time.sleep(2)

        t1 = time.time()
        result = subprocess.run([
            "curl", "--socks5", "127.0.0.1:10808", "-m", "6",
            "-s", "-o", "/dev/null", "https://www.google.com"
        ])
        t2 = time.time()

        xray_proc.terminate()

        if result.returncode == 0:
            return {"success": True, "latency": int((t2 - t1) * 1000)}
        else:
            return {"success": False, "error": "request failed"}

    except Exception as e:
        return {"success": False, "error": str(e)}, 500

def parse_vmess(link):
    encoded = link.replace("vmess://", "")
    padded = encoded + "=" * (-len(encoded) % 4)
    decoded = base64.b64decode(padded).decode()
    return json.loads(decoded)

def generate_xray_config(v):
    return {
        "inbounds": [{
            "port": 10808,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"auth": "no_auth"}
        }],
        "outbounds": [{
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": v["add"],
                    "port": int(v["port"]),
                    "users": [{
                        "id": v["id"],
                        "alterId": int(v.get("aid", 0)),
                        "security": v.get("scy", "auto")
                    }]
                }]
            },
            "streamSettings": {
                "network": v.get("net", "tcp"),
                "security": v.get("tls", ""),
                "wsSettings": {
                    "path": v.get("path", ""),
                    "headers": {
                        "Host": v.get("host", "")
                    }
                } if v.get("net") == "ws" else {}
            }
        }]
    }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
