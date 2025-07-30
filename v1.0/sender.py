
from utils import send_udp_message_and_receive_response, get_fronius_powerflow_data

response = send_udp_message_and_receive_response("ena 1")
if response:
    print("Received:", response.decode(errors="replace"))
else:
    send_udp_message_and_receive_response("ena 1")


