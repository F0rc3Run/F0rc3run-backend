import os
import ipaddress
import random
import time
import threading
import socket
from datetime import datetime

# ---------------- CONFIG ----------------
IPV4_RANGES = [
    "162.159.192.0/24", "162.159.193.0/24", "162.159.195.0/24",
    "162.159.204.0/24", "188.114.96.0/24", "188.114.97.0/24",
    "188.114.98.0/24", "188.114.99.0/24"
]
CONFIG_PORTS = [2408, 1701, 500, 4500, 8886, 908]
MAX_IPS_PER_RANGE = 25
MAX_THREADS = 200
TCP_TIMEOUT = 1.5
OUTPUT_FILE = "endpoints.txt"
# -----------------------------------------

def generate_endpoints(ip_ranges):
    endpoints = set()
    for cidr in ip_ranges:
        try:
            net = ipaddress.ip_network(cidr)
            hosts = list(net.hosts())
            sample_size = min(len(hosts), MAX_IPS_PER_RANGE)
            ip_sample = random.sample(hosts, sample_size)
            for ip in ip_sample:
                for port in CONFIG_PORTS:
                    endpoints.add(f"{ip}:{port}")
        except Exception:
            pass
    endpoints = list(endpoints)
    random.shuffle(endpoints)
    return endpoints

def tcp_scan_worker(endpoint, results, lock, progress, total):
    try:
        ip, port_str = endpoint.rsplit(':', 1)
        port = int(port_str)
        start = time.time()
        with socket.create_connection((ip, port), timeout=TCP_TIMEOUT):
            latency = (time.time() - start) * 1000
            with lock:
                results.append({"endpoint": endpoint, "latency": latency})
    except Exception:
        pass
    finally:
        with lock:
            progress["done"] += 1
            print(f"\rScanning {progress['done']}/{total}", end="", flush=True)

def perform_scan(endpoints):
    results, threads = [], []
    lock = threading.Lock()
    progress = {"done": 0}
    total = len(endpoints)

    for ep in endpoints:
        t = threading.Thread(target=tcp_scan_worker, args=(ep, results, lock, progress, total))
        threads.append(t)
        t.start()
        if len(threads) >= MAX_THREADS:
            for th in threads: th.join()
            threads = []
    for th in threads: th.join()

    return sorted(results, key=lambda x: x["latency"])

def main():
    print(">>> Generating endpoints...")
    endpoints = generate_endpoints(IPV4_RANGES)
    print(f"Generated {len(endpoints)} endpoints.")

    print(">>> TCP Scanning...")
    results = perform_scan(endpoints)

    if not results:
        print("No valid endpoints found.")
        return

    top20 = results[:20]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Top 20 Endpoints - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for r in top20:
            f.write(f"{r['endpoint']}, {r['latency']:.2f} ms\n")

    print(f"\n>>> Top 20 endpoints saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
