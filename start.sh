#!/bin/bash

echo "📦 Downloading xray-core..."
curl -L -o xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip
unzip xray.zip
chmod +x xray

echo "🚀 Starting backend..."
python3 main.py
