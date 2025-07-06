
from utils import send_udp_message_and_receive_response, get_fronius_powerflow_data

response = send_udp_message_and_receive_response("ena 1")
if response:
    print("Received:", response.decode(errors="replace"))
else:
    send_udp_message_and_receive_response("ena 1")

data = get_fronius_powerflow_data()
pv_power = data.get("P_PV", 0)
grid_power = data.get("P_Grid", 0)
load_power = data.get("P_Load", 0)
battery_power = data.get("P_Akku", 0)
battery_soc = data.get("SOC", 0)

curr_amp = 6000 # can be betweeen 6000 and 63000 is in mA

charging_power = (curr_amp /1000) * 3 * 230 # three phase charging at 230V



if data:
    print("PV Power:      ", pv_power, "W")
    print("Grid Power:    ", grid_power, "W")
    print("Load Power:    ", load_power, "W")
    print("Battery Power: ", battery_power, "W")
    print("Battery SOC:   ", battery_soc, "%")
else:
    print("No data received.")
