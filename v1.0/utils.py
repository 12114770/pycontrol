import socket
import select
import requests
from datetime import datetime, timedelta

def get_sun_hours_eichstaett(threshold=120):
    """
    Fetches solar radiation for Eichstätt, Germany and estimates sun hours in next 48h.
    :param threshold: Radiation threshold (W/m²) to count as sun hour
    :return: Estimated sun hours (int)
    """
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

    now = datetime.now()
    end = now + timedelta(hours=48)

    sun_hours = 0
    for t_str, rad in zip(data["hourly"]["time"], data["hourly"]["shortwave_radiation"]):
        t = datetime.fromisoformat(t_str)
        if now <= t <= end and rad is not None and rad > threshold:
            sun_hours += 1

    return sun_hours





def send_udp_message_and_receive_response(message, ip="192.168.178.59", port=7090, timeout=2):
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

def get_fronius_powerflow_data(ip="192.168.178.33"):
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
