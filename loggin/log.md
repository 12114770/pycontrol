## Setup

- Made Ethernet connection using a wifi extender 
- finding ip address using the app of the extender
    - can be tricky
- no connection possible
- found out dpi switches were configured wrong
- still no tcp connection (for direct modbus)
- could establish that udp port 7090 was open, but no response
- confirming via wireshark and looking at decoded bytepattern that wallbox respondes
    - netcat had a bug, and my pc sends a destination unreachable back
- socat had similar behaviour, but with 
```
(socat -T2 - udp-recvfrom:7090 > /tmp/udp_response.txt &) && sleep 0.2 && echo -n "i" | socat - udp-sendto:192.168.178.59:7090 && sleep 2 && cat /tmp/udp_response.txt
```
i got the response 
```
"Firmware":"P30 v 3.10.27 (210105-174852)"
```
and i could not detect any icmp error messages.

## evcc as translation layer
### setup evcc
- froenius can only send modbus tcp, so i will try to use a evcc as a translation layer.
- i connect raspberry to power and do a network scan to find mac and ip . 
- then try old passwords to login
- setup wireguard vpn on raspberry too
- disable wireguard to install evcc
- compile with go 

### setup evcc 
 create config file 
```
mkdir -p ~/.evcc
nano ~/.evcc/config.yaml
```
evcc did not work
### switching over to pyhton + grafana

setting up influx db

making a fastapp api

tried using the pushbotton togehter with fastapi
 
although 
```
curl -X POST http://localhost:8090/boost
```
worked, the grafana button did not activate the boost

enabled 
```
disable_sanitize_html = true
```

and with 

grafana text field and  

```
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
i was able to add button.


### making acces from anywhere



#### Install ngrok:
```
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```


Create a free account at https://dashboard.ngrok.com and get your auth token.

Authenticate:

```
ngrok config add-authtoken <your_token_here>
```

Start the tunnel:
```
ngrok http 3000
```

You’ll get a public HTTPS URL like:
```
https://f9a2-203-0-113-42.ngrok.io
```
now you can just paste this and use it normally from anywhere



#### configure ngix, to do local loopback

```
sudo nano /etc/nginx/sites-available/grafana_boost
```

and paste

```
sudo nano /etc/nginx/sites-available/grafana_boost


```
and reload 

```
sudo nginx -t && sudo systemctl reload nginx
```
 now restart ngrok with unified access

 ```
 ngrok http 80
 ```

##### use lxc to run mutliple instances at once 


```
sudo apt update
sudo apt install lxd -y
```

```
sudo lxd init
```

    Use these answers:

    Clustering: no

    Storage: yes, backend: dir

    Bridge: yes, name: lxdbr0

    IPv4: auto, IPv6: none

    Remote access: no




```
lxc launch ubuntu:22.04 haus1
```




```
lxc file push -r ~/pycontrol haus1/home/ubuntu/

```

```
lxc exec haus1 -- bash

```

```
apt update
apt install -y python3 python3-pip wireguard influxdb grafana
```

```
lxc launch ubuntu:22.04 haus1
```

then enter the container via 

```
lxc exec haus1 -- bash
```

run setup script then when the influxdb command prompt opens do 
```
CREATE DATABASE fronius;
SHOW DATABASES;
exit
```

back in the lxc container 

```
sudo nano /etc/hosts
```

and paste the line 
```
127.0.1.1   haus1
```
then restart nginx

```
sudo nginx -t && sudo systemctl reload nginx
```

on host forward the port 
```
lxc config device add haus1 nginxport80 proxy listen=tcp:0.0.0.0:80 connect=tcp:127.0.0.1:80
```

You're right — thanks for catching that!

Here's an updated and complete start_all.sh script that starts:

    main.py

    uvicorn boost_api

    nginx

    grafana

    ngrok (with reserved domain)

✅ Full Script: start_all.sh

✅ Make it executable:

chmod +x start_all.sh

✅ Run it:

./start_all.sh

🔍 Check status:

ps aux | grep python
ps aux | grep uvicorn
ps aux | grep ngrok
systemctl status nginx
systemctl status grafana-server

Or watch logs live:

tail -f main.log uvicorn.log ngrok.log

Let me know if you want a matching stop_all.sh, or turn this into a boot-time systemd unit!
You said:
but this does not autostart
ChatGPT said:

You're absolutely right again — the start_all.sh script runs manually but does not autostart on boot.

Let’s fix that by creating a systemd service that runs your start_all.sh automatically at container or system boot.
✅ Step-by-Step: Autostart start_all.sh with systemd
🧾 1. Create the service unit

sudo nano /etc/systemd/system/pycontrl.service

Paste this:

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

    🔁 Adjust paths if you're not in /root or if you move the script.

🔓 2. Make sure your script is executable

chmod +x /root/pycontrl/v1.1/start_all.sh

🚀 3. Enable and start the service

sudo systemctl daemon-reload
sudo systemctl enable pycontrl.service
sudo systemctl start pycontrl.service

🧪 4. Check it worked

sudo systemctl status pycontrl.service

You should see something like:

Active: active (running)

Check logs if needed:

tail -f /root/pycontrl/v1.1/systemd.log
tail -f /root/pycontrl/v1.1/systemd.err.log

✅ Done!

Your entire system — Python logic, FastAPI server, NGINX, Grafana, and ngrok — now autostarts on boot.

Let me know if you want a stop_all.sh script, restart logic, or ngrok health checks too.


ChatGPT can make mistakes. Check important info. See Cookie Preferences.


### tried to pull data from car

client wanted to be able to make that car only charges to 80% soc.

smartcar was commercial, needed license.

tried using psa_car_controller



