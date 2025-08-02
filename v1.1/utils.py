import socket
import select
import requests
from datetime import datetime, timedelta
import os

BOOST_FILE = "/tmp/boost_until"

import traceback

import os
import json
import time

SUN_CACHE_FILE = "/tmp/sun_hours_cache.json"
CACHE_DURATION = 3600  # 1 hour


FRONIUS_IP = "192.168.178.33"
KEBA_IP = "192.168.178.59"



def get_sun_hours_eichstaett(threshold=120):
    now = time.time()
    # Check cache
    if os.path.exists(SUN_CACHE_FILE):
        try:
            with open(SUN_CACHE_FILE, "r") as f:
                cache = json.load(f)
                if now - cache["timestamp"] < CACHE_DURATION:
                    return cache["sun_hours"]
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")

    try:
        lat = 48.8885
        lon = 11.1863
        tz = "Europe/Berlin"
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&hourly=shortwave_radiation"
            f"&timezone={tz}"
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        now_dt = datetime.now()
        end = now_dt + timedelta(hours=48)

        sun_hours = 0
        for t_str, rad in zip(data["hourly"]["time"], data["hourly"]["shortwave_radiation"]):
            t = datetime.fromisoformat(t_str)
            if now_dt <= t <= end and rad is not None and rad > threshold:
                sun_hours += 1

        # Save to cache
        with open(SUN_CACHE_FILE, "w") as f:
            json.dump({"timestamp": now, "sun_hours": sun_hours}, f)

        return sun_hours

    except Exception as e:
        print("⚠️ Error fetching sun hours data")
        print(e)
        return 16




def send_udp_message_and_receive_response(message, ip=KEBA_IP, port=7090, timeout=2):
    """
    Sends a UDP message and returns the response.

    :param message: The message to send (str or bytes)
    :param ip: Target IP address
    :param port: Target UDP port
    :param timeout: Timeout in seconds to wait for a response
    :return: Response from the server as bytes, or None if no response
    """
    if isinstance(message, str):
        message = message.encode()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', port))  # Bind to same port to receive response (optional)
        sock.setblocking(0)

        sock.sendto(message, (ip, port))

        ready = select.select([sock], [], [], timeout)
        if ready[0]:
            data, _ = sock.recvfrom(4096)
            return data
        else:
            return None

def get_fronius_powerflow_data(ip=FRONIUS_IP):
    """
    Queries the Fronius inverter for real-time power flow data.

    :param ip: IP address of the Fronius device
    :return: A dictionary with PV, Grid, Load, Battery power and SOC
    """
    url = f"http://{ip}/solar_api/v1/GetPowerFlowRealtimeData.fcgi"

    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        data = response.json()

        site = data["Body"]["Data"]["Site"]
        inverter = data["Body"]["Data"]["Inverters"]["1"]

        return {
            "P_PV": site.get("P_PV", 0),
            "P_Grid": site.get("P_Grid", 0),
            "P_Load": site.get("P_Load", 0),
            "P_Akku": site.get("P_Akku", 0),
            "SOC": inverter.get("SOC", 0),
        }

    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"Error retrieving power flow data: {e}")
        return None

def push_to_influxdb(data: dict, measurement="ev_power", influx_url="http://localhost:8086/write?db=fronius"):
    """
    Push Fronius data dict to InfluxDB.
    """
    # Build line protocol format
    line = f"{measurement} pv={data.get('P_PV',0)},grid={data.get('P_Grid',0)},load={data.get('P_Load',0)},soc={data.get('SOC',0)},sun_hours={data.get('sun_hours',0)},boost_remaining={data.get('boost_remaining',0)},temp_remaining={data.get('temp_remaining',0)}"

    try:
        resp = requests.post(influx_url, data=line)
        if resp.status_code != 204:
            print(f"❌ InfluxDB write failed: {resp.status_code}, {resp.text}")
        else:
            print("✅ Wrote data to InfluxDB")
    except Exception as e:
        print(f"❌ Could not write to InfluxDB: {e}")





def is_boost_active():
    global boost_remaining 
    try:
        if os.path.exists(BOOST_FILE):
            with open(BOOST_FILE) as f:
                ts = int(f.read())
                boost_remaining = datetime.fromtimestamp(ts)
                return datetime.now() <boost_remaining 
    except Exception as e:
        print(f"⚠️ Boost check failed: {e}")
    return False
