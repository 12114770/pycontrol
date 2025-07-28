#!/bin/bash

cd "$(dirname "$0")"  # move to script directory

# Activate virtual environment
source ./ctrlvenv/bin/activate

echo "▶️ Starting main.py..."
nohup python3 main.py > main.log 2>&1 &

echo "▶️ Starting boost_api (uvicorn)..."
nohup ./ctrlvenv/bin/uvicorn boost_api:app --host 0.0.0.0 --port 8090 > uvicorn.log 2>&1 &

echo "▶️ Starting nginx..."
systemctl start nginx

echo "▶️ Starting grafana..."
systemctl start grafana-server

echo "▶️ Starting ngrok on reserved domain..."
nohup ngrok http --domain=wildcat-actual-previously.ngrok-free.app 80 > ngrok.log 2>&1 &

echo "✅ All services started. Check logs for output."
