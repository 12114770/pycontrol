## Setup

The initial setup involved connecting the EV wallbox to the local network using an Ethernet cable routed through a Wi-Fi extender. Identifying the correct IP address of the wallbox required the use of the extender’s mobile app, which proved to be a somewhat tricky process. Despite the connection appearing active, no communication with the wallbox was possible at first.

Upon closer inspection, it was discovered that the DIP switches on the wallbox were incorrectly configured. After correcting them, attempts to communicate via TCP (for direct Modbus access) still failed. However, a scan revealed that UDP port 7090 was open, suggesting potential for alternative communication.

Initial tests using `netcat` yielded no results. In fact, the PC responded with “destination unreachable” ICMP messages, indicating that no valid response was received from the wallbox. Similar behavior was observed with `socat`. Nevertheless, after some trial and error, communication was successfully established using the following `socat` command:

```bash
(socat -T2 - udp-recvfrom:7090 > /tmp/udp_response.txt &) && sleep 0.2 && echo -n "i" | socat - udp-sendto:192.168.178.59:7090 && sleep 2 && cat /tmp/udp_response.txt
```

This command prompted the wallbox to respond with the firmware version string:

```json
"Firmware":"P30 v 3.10.27 (210105-174852)"
```

This confirmed that the wallbox was reachable and responsive over UDP, and no ICMP errors were observed during successful exchanges. The response pattern also aligned with data observed earlier using Wireshark, confirming correct byte decoding and validating the communication pathway.

## EVCC as Translation Layer

### Setup EVCC

Since the Fronius inverter only communicates via Modbus TCP, the initial idea was to use EVCC as a translation layer that could bridge this protocol to the wallbox. The Raspberry Pi was connected to power, and a network scan was performed to identify its MAC address and IP. After locating the device on the network, several previously used passwords were tried until access was successfully regained.

A WireGuard VPN was set up on the Raspberry Pi to allow remote administration and monitoring. However, to avoid potential conflicts during installation, the WireGuard service was temporarily disabled. The EVCC software was then compiled manually using Go.

### EVCC Configuration

To begin configuring EVCC, a directory for the configuration file was created, and a new configuration file was opened for editing:

```bash
mkdir -p ~/.evcc
nano ~/.evcc/config.yaml
```

Despite completing the installation and configuration steps, EVCC did not function in this setup. The core issue was that EVCC only supports TCP-based communication, whereas the KEBA KC30 wallbox requires UDP. This incompatibility made it impossible to proceed with EVCC as a viable solution for this project.


## Switching to Python + Grafana

After EVCC was ruled out, the project pivoted toward a custom solution using Python, FastAPI, InfluxDB, and Grafana. The first step was to set up the InfluxDB time-series database to store energy and charging data.

InfluxDB was installed using the system package manager:

```bash
sudo apt update
sudo apt install influxdb
```

Once the service was running, the Influx shell was launched with the `influx` command. Inside the shell, a new database was created to store Fronius and charging metrics:

```sql
CREATE DATABASE fronius;
SHOW DATABASES;
exit
```### tried to pull data from car

client wanted to be able to make that car only charges to 80% soc.

smartcar was commercial, needed license.

tried using psa_car_controller
 
this works, i configured it and can now adjust charging using 



@app.post("/charge_limit-80")
def set_charge_limit_80():
    url = f"http://{SERVER_IP}:5000/charge_control?vin={VIN}&percentage=80"
    try:
        r = requests.get(url)
        return {
            "message": "Charging limit set to 80%",
            "response": r.text,
            "status": r.status_code
        }
    except Exception as e:
        print("wrong Vin")
        return {"error": str(e)}

Next, Grafana was installed and configured to visualize the data:

```bash
sudo apt install grafana
```

Grafana was started and enabled to launch on boot:

```bash
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

It was connected to the InfluxDB instance by adding a new data source via the Grafana UI. The URL `http://localhost:8086` was used, with the selected database set to `fronius`. No authentication was required in the default setup.

With the database and visualization layers in place, a FastAPI backend was developed to serve a REST API. This API included endpoints for controlling the wallbox (e.g., boosting and stopping charge). To run the FastAPI application, `uvicorn` was used as the ASGI server:

```bash
uvicorn boost_api:app --host 0.0.0.0 --port 8090
```

Testing the endpoint with `curl` confirmed that the backend worked as expected:

```bash
curl -X POST http://localhost:8090/boost
```

However, the Grafana dashboard button initially failed to activate the boost. This was due to HTML sanitization in Grafana, which stripped out JavaScript from text panels. To resolve this, the Grafana configuration file (`grafana.ini`) was edited to include the line:

```ini
disable_sanitize_html = true
```

Grafana was then restarted with:

```bash
sudo systemctl restart grafana-server
```

Once HTML sanitization was disabled, a custom button could be embedded inside a Grafana text panel using the following HTML and JavaScript:

```html
<div style="display: flex; flex-direction: column; gap: 10px; align-items: flex-start;">
  <button 
    style="font-size: 18px; padding: 12px 20px; background-color: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer;"
    onclick="fetch('http://192.168.0.106:8090/boost', { method: 'POST' })
      .then(res => {
        if (res.ok) {
          alert('✅ Boost activated!');
        } else {
          alert('❌ Boost activation failed.');
        }
      }).catch(err => alert('⚠️ Network error: ' + err))">
    🚀 Boost Charging
  </button>

  <button 
    style="font-size: 18px; padding: 12px 20px; background-color: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer;"
    onclick="fetch('http://192.168.0.106:8090/stop-boost', { method: 'POST' })
      .then(res => {
        if (res.ok) {
          alert('🛑 Boost stopped!');
        } else {
          alert('❌ Failed to stop boost.');
        }
      }).catch(err => alert('⚠️ Network error: ' + err))">
    🛑 Stop Boost
  </button>
</div>
```

After adding this to the Grafana text panel and saving the dashboard, the buttons successfully triggered the FastAPI backend. This allowed full control over boost charging from the Grafana web interface.

### Exposing the Dashboard with ngrok and Configuring NGINX

To make the Grafana dashboard accessible from anywhere, **ngrok** was used to tunnel local HTTP traffic to a public domain. The following commands were used to install ngrok on the Raspberry Pi:

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

After installation, a free ngrok account was created at [https://dashboard.ngrok.com](https://dashboard.ngrok.com), and the personal auth token was retrieved. This token was added to the system using:

```bash
ngrok config add-authtoken <your_token_here>
```

With authentication complete, the tunnel was started:

```bash
ngrok http 3000
```

This exposed the local Grafana instance (running on port 3000) to a public HTTPS URL such as:

```
https://f9a2-203-0-113-42.ngrok.io
```

This public URL can now be accessed from any device with an internet connection, allowing remote control and monitoring of the smart charging system.

---

To route local traffic internally, **NGINX** was configured as a reverse proxy. This allowed ngrok to forward to port `80` locally, even though Grafana itself listens on port `3000`. The configuration file was created by opening:

```bash
sudo nano /etc/nginx/sites-available/grafana_boost
```

The following content was added (assuming Grafana is running on port 3000):

```nginx
server {
    listen 80;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

The site was then enabled by linking it into the `sites-enabled` directory and disabling the default config:

```bash
sudo ln -sf /etc/nginx/sites-available/grafana_boost /etc/nginx/sites-enabled/grafana_boost
sudo rm -f /etc/nginx/sites-enabled/default
```

After verifying the configuration is valid:

```bash
sudo nginx -t
```

NGINX was reloaded to apply the changes:

```bash
sudo systemctl reload nginx
```

With NGINX acting as a proxy, ngrok was restarted t### tried to pull data from car

client wanted to be able to make that car only charges to 80% soc.

smartcar was commercial, needed license.

tried using psa_car_controller
 
this works, i configured it and can now adjust charging using 



@app.post("/charge_limit-80")
def set_charge_limit_80():
    url = f"http://{SERVER_IP}:5000/charge_control?vin={VIN}&percentage=80"
    try:
        r = requests.get(url)
        return {
            "message": "Charging limit set to 80%",
            "response": r.text,
            "status": r.status_code
        }
    except Exception as e:
        print("wrong Vin")
        return {"error": str(e)}o tunnel port `80` instead of `3000` directly:

```bash
ngrok http 80
```

Now the public ngrok URL would serve the Grafana dashboard via NGINX, enabling access from anywhere with a consistent structure.


## Running Multiple Instances with LXC and Enabling Autostart

To isolate environments for different homes or test setups, the system was deployed using LXC containers. This allows multiple instances of the EV charging control stack to run in parallel on the same physical host.

### LXC Setup

First, LXD was installed and initialized:

```bash
sudo apt update
sudo apt install lxd -y
sudo lxd init
```

During initialization, the following answers were provided:

- Clustering: **no**  
- Storage: **yes**, backend: **dir**  
- Bridge: **yes**, name: **lxdbr0**  
- IPv4: **auto**, IPv6: **none**  
- Remote access: **no**

With LXD ready, a new container was launched:

```bash
lxc launch ubuntu:22.04 haus1
```

To ensure NGINX inside the container resolves its own hostname correctly, the following line was added to `/etc/hosts` inside the container:

```bash
127.0.1.1   haus1
```

Then, NGINX was reloaded:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

On the **host**, port forwarding was enabled so external access to port 80 reaches the container:

```bash
lxc config device add haus1 nginxport80 proxy listen=tcp:0.0.0.0:80 connect=tcp:127.0.0.1:80
```

#### Automating Service Startup with systemd

To ensure the charging system automatically starts at container boot, a `start_all.sh` script was written inside the container at `/root/pycontrl/v1.1/start_all.sh`. This script starts:

- `main.py` (Python logic)
- `boost_api` via `uvicorn`
- `nginx`
- `grafana-server`
- `ngrok` with reserved domain

Sample content of `start_all.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")"

source ../ctrlvenv/bin/activate

echo "▶️ Starting main.py..."
nohup python3 main.py > main.log 2>&1 &

echo "▶️ Starting boost_api..."
nohup ../ctrlvenv/bin/uvicorn boost_api:app --host 0.0.0.0 --port 8090 > uvicorn.log 2>&1 &

echo "▶️ Starting nginx..."
systemctl start nginx

echo "▶️ Starting grafana..."
systemctl start grafana-server

echo "▶️ Starting ngrok on reserved domain..."
nohup ngrok http --domain=your-ngrok-domain.ngrok-free.app 80 > ngrok.log 2>&1 &

echo "✅ All services started."
```

Make the script executable:

```bash
chmod +x /root/pycontrl/v1.1/start_all.sh
```

Then create a systemd service file:

```bash
sudo nano /etc/systemd/system/pycontrl.service
```

Insert the following content:

```ini
[Unit]
Description=Start pycontrl EV Charging System
After=network.target grafana-server.service nginx.service

[Service]
Type=simple
WorkingDirectory=/root/pycontrl/v1.1
ExecStart=/bin/bash /root/pycontrl/v1.1/start_all.sh
Restart=on-failure
StandardOutput=append:/root/pycontrl/v1.1/systemd.log
StandardError=append:/root/pycontrl/v1.1/systemd.err.log

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pycontrl.service
sudo systemctl start pycontrl.service
```

Verify that it's running:

```bash
sudo systemctl status pycontrl.service
```

Expected status:

```
Active: active (running)
```

If needed, monitor logs live:

```bash
tail -f /root/pycontrl/v1.1/systemd.log
tail -f /root/pycontrl/v1.1/systemd.err.log
```

With this setup, every time the LXC container boots, the entire smart charging system — including your Python scripts, FastAPI backend, Grafana dashboard, NGINX proxy, and ngrok tunnel — starts automatically and is ready to use.


## Charging Limit via Car API

One requirement from the client was the ability to limit vehicle charging to a specific state of charge (SOC), such as 80%. Initially, the [Smartcar API](https://smartcar.com/) was evaluated for this purpose, but it required a commercial license and was therefore not feasible for this project.

Instead, the open-source [`psa_car_controller`](https://github.com/flobz/psa_car_controller) project was used to interact with the vehicle. This tool proved effective for sending commands like setting a charge limit or reading SOC values from compatible Peugeot/Citroën electric vehicles.

After proper configuration of the controller (which includes setting up the correct VIN and IP address for the vehicle or emulator backend), charging limits could be adjusted via a RESTful endpoint.

Example FastAPI route for setting an 80% charge limit:

```python
@app.post("/charge_limit-80")
def set_charge_limit_80():
    url = f"http://{SERVER_IP}:5000/charge_control?vin={VIN}&percentage=80"
    try:
        r = requests.get(url)
        return {
            "message": "Charging limit set to 80%",
            "response": r.text,
            "status": r.status_code
        }
    except Exception as e:
        print("wrong Vin")
        return {"error": str(e)}
```

The FastAPI route issues a simple HTTP GET request to the `psa_car_controller` API, passing the desired SOC percentage as a query parameter. Upon success, the system confirms that the limit has been set, or otherwise logs the error — such as an incorrect or missing VIN.

This integration enabled automated or button-controlled charge limiting from within the existing smart charging dashboard.
