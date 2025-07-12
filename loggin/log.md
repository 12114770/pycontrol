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






```

```



### tried to pull data from car

client wanted to be able to make that car only charges to 80% soc.

smartcar was commercial, needed license.

tried using psa_car_controller



