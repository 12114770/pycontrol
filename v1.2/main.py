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


CHARGING_VOLTAGE = 230
PHASES = 3
CHECK_INTERVAL = 1 # seconds

boost_active_until = None
charging = False
charging_current = 6000  # default current in mA


def control_charging():
    
    global boost_active_until, charging, temp_until_ts, charging_current

    data = get_fronius_powerflow_data()
    if not data:
        print("❌ No data received.")
        return
    

    if data["P_PV"] is None:
        data["P_PV"] = 0  # Ensure PV power is not None
    if data["P_Grid"] is None:
        data["P_Grid"] = 0
    if data["P_Load"] is None:
        data["P_Load"] = 0
    if data["SOC"] is None:
        data["SOC"] = 0
    
    
    # In control_charging():
    try:
        with open("/tmp/boost_until", "r") as f:
            boost_until_ts = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        boost_until_ts = 0
    
    try:
        with open("/tmp/temporary_charge_until", "r") as f:
            temp_until_ts = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        temp_until_ts = 0
    




    
    now = time.time()
    remaining = max(0, int(boost_until_ts - now))
    data["boost_remaining"] = remaining  # in seconds
    print(f"Boost remaining: {remaining} seconds")
    temp_remaining = max(0, int(temp_until_ts - now))
    data["temp_remaining"] = temp_remaining
    print(f"Temporary charge remaining: {temp_remaining} seconds")
    
    push_to_influxdb(data)

    pv = data["P_PV"]
    grid = data["P_Grid"]
    load = data["P_Load"]
    soc = data["SOC"]
    sun_hours = get_sun_hours_eichstaett()





    print(f"🔍 PV: {pv} | Grid: {grid} | Load: {load} | SOC: {soc}% | Sun: {sun_hours}h")
    try:
        if is_boost_active():
            send_udp_message_and_receive_response("ena 1")
            print("🚀 Boost mode active – skipping control logic")
            return
        if temp_remaining> 0:
            send_udp_message_and_receive_response("ena 1")
            print("⚡ Temporary charge mode active – skipping logic")
            charging = True
            return

        charging_power = (charging_current / 1000) * CHARGING_VOLTAGE * PHASES
        if charging== True:
            power_budget = pv + load + charging_power
            if power_budget > charging_power + 500:
                charging_power = power_budget -pv- load  
                charging_current = int((power_budget / (CHARGING_VOLTAGE * PHASES)) * 1000)
                send_udp_message_and_receive_response("curr" + str(charging_current))
                 

        else:
            power_budget = pv + load

        now = time.time()

        if soc < 50:
            print("🛑 SOC < 50% – disabling charging")
            send_udp_message_and_receive_response("ena 0")
            charging = False
            last_disable_time = now  # ⬅️ set cooldown
        elif soc > 50:
            if sun_hours < 16:
                print("🛑 Not enough sun despite SOC > 50% – disabling charging")
                send_udp_message_and_receive_response("ena 0")
                charging = False
                last_disable_time = now
            elif power_budget > charging_power:
                # ⬇️ check cooldown period
                if now - last_disable_time >= 10:
                    print("✅ Enabling charging – enough PV available and cooldown passed")
                    send_udp_message_and_receive_response("ena 1")
                    charging = True
                else:
                    print(f"⏱️ Cooldown active – waiting to enable (remaining {int(10 - (now - last_disable_time))}s)")
            else:
                print("🛑 Not enough PV – disabling charging")
                send_udp_message_and_receive_response("ena 0")
                charging = False
                last_disable_time = now

    except Exception as e:
        print(f"❌ Error in control logic: {e}")
        send_udp_message_and_receive_response("ena 0")
        charging = False
        return


if __name__ == "__main__":
    print("🟢 Starting Smart Charging Logic")
    while True:
        control_charging()
        time.sleep(CHECK_INTERVAL)
