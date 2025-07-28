echo "🔧 Starting haus1 container setup..."

# 1. Create venv & install Python deps
cd /root/pycontrl
python3 -m venv ctrlvenv
source ctrlvenv/bin/activate
pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn requests influxdb

apt install influxdb-client

influx

# 2. Restore configs
echo "🔁 Restoring config files..."

# Grafana
cp grafana/grafana.ini /etc/grafana/
cp grafana/grafana.db /var/lib/grafana/

# NGINX
cp nginx/nginx.conf /etc/nginx/
cp nginx/grafana_boost /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/grafana_boost /etc/nginx/sites-enabled/grafana_boost
rm -f /etc/nginx/sites-enabled/default

# InfluxDB
cp influxdb/influxdb.conf /etc/influxdb/

# Restart services
systemctl restart grafana-server influxdb nginx


apt update
apt install -y wireguard
apt install -y resolvconf


systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0


uvicorn boost_api:app --host 0.0.0.0 --port 8090 &


