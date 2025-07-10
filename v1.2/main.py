# main.py

from utils import   (
                        get_fronius_powerflow_data,
                        get_sun_hours_eichstaett,
                        send_udp_message_and_receive_response,
                        push_to_influxdb,
                        is_boost_active
                    )
from datetime import datetime, timedelta
import time

CHARGING_CURRENT = 6000
CHARGING_VOLTAGE = 230
PHASES = 3
CHECK_INTERVAL = 1 # seconds

boost_active_until = None
charging = False



def control_charging():
    global boost_active_until, charging

    data = get_fronius_powerflow_data()
    if not data:
        print("❌ No data received.")
        return
    
    
    # In control_charging():
    try:
        with open("/tmp/boost_until", "r") as f:
            boost_until_ts = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        boost_until_ts = 0

    
    now = time.time()
    remaining = max(0, int(boost_until_ts - now))

    data["boost_remaining"] = remaining  # in seconds
    print(f"Boost remaining: {remaining} seconds")
    push_to_influxdb(data)

    pv = data["P_PV"]
    grid = data["P_Grid"]
    load = data["P_Load"]
    soc = data["SOC"]
    sun_hours = get_sun_hours_eichstaett()



    print(f"🔍 PV: {pv} | Grid: {grid} | Load: {load} | SOC: {soc}% | Sun: {sun_hours}h")

    if is_boost_active():
        print("🚀 Boost mode active – skipping control logic")
        return

    charging_power = (CHARGING_CURRENT / 1000) * CHARGING_VOLTAGE * PHASES
    if charging== True:
        power_budget = pv + load- charging_power
    else:
        power_budget = pv + load

    if soc < 50:
        print("🛑 SOC < 30% – disabling charging")
        send_udp_message_and_receive_response("ena 0")
        charging = False
    elif soc > 50:
        if sun_hours < 16:
            print("🛑 Not enough sun despite SOC > 50% – disabling charging")
            send_udp_message_and_receive_response("ena 0")
            charging = False
        elif power_budget > charging_power:
            print("✅ Enabling charging – enough PV available")
            send_udp_message_and_receive_response("ena 1")
            charging = True
        else:
            print("🛑 Not enough PV – disabling charging")
            send_udp_message_and_receive_response("ena 0")
            charging = False



if __name__ == "__main__":
    print("🟢 Starting Smart Charging Logic")
    while True:
        control_charging()
        time.sleep(CHECK_INTERVAL)
