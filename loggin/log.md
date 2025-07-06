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

