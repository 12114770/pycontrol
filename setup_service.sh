#!/bin/bash

echo "🔧 Starting haus1 container setup..."

# --- Save script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Ensure apt is up to date
echo "🧰 Updating package list..."
apt update -y

# --- Install required tools
echo "⬇️ Installing dependencies..."
apt install -y unzip influxdb-client nginx grafana

# --- Create Python virtual environment
cd /root/pycontrl
if [ ! -d ctrlvenv ]; then
    echo "🐍 Creating Python venv..."
    python3 -m venv ctrlvenv
fi

source ctrlvenv/bin/activate

# --- Install Python packages
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install fastapi uvicorn requests influxdb
fi

# --- Copy InfluxDB config
echo "📈 Setting up InfluxDB..."
cp influxdb/influxdb.conf /etc/influxdb/
systemctl restart influxdb

# --- Set up Grafana dashboard
echo "📊 Setting up Grafana..."
mkdir -p /etc/grafana/dashboards
cp v1.2/grafana/hubert_dashboard.json /etc/grafana/dashboards/

systemctl restart grafana-server

# --- Configure NGINX
echo "🌐 Configuring NGINX..."
cp nginx/nginx.conf /etc/nginx/
cp nginx/grafana_boost /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/grafana_boost /etc/nginx/sites-enabled/grafana_boost
rm -f /etc/nginx/sites-enabled/default

systemctl restart nginx

# --- Install ngrok
echo "🕳️ Installing ngrok..."
cd /usr/local/bin
wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-arm.zip -O ngrok.zip
unzip -o ngrok.zip
chmod +x ngrok
rm ngrok.zip
cd "$SCRIPT_DIR"

# --- Setup ngrok authtoken if missing
if ! grep -q "authtoken" ~/.config/ngrok/ngrok.yml 2>/dev/null; then
    echo "🔐 No ngrok authtoken found."
    read -p "Please enter your ngrok authtoken: " TOKEN
    ngrok config add-authtoken "$TOKEN"
fi

echo "✅ All setup tasks completed."
echo "💡 Now run: ./start_all.sh to launch all services."

#apt install -y wireguard
#apt install -y resolvconf


#systemctl enable wg-quick@wg0
#systemctl start wg-quick@wg0



