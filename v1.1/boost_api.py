from fastapi import FastAPI
from datetime import datetime, timedelta
from utils import send_udp_message_and_receive_response, is_boost_active

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global boost time file
BOOST_FILE = "/tmp/boost_until"

@app.post("/boost")
def activate_boost():
    boost_until = datetime.now() + timedelta(hours=5)
    with open(BOOST_FILE, "w") as f:
        f.write(str(int(boost_until.timestamp())))
    send_udp_message_and_receive_response("curr 16000")
    send_udp_message_and_receive_response("ena 1")
    return {"message": "Boost activated", "until": boost_until.isoformat()}


@app.post("/stop-boost")
def stop_boost():
    with open(BOOST_FILE, "w") as f:
        f.write("0")
    send_udp_message_and_receive_response("curr 6000")  # reset to normal current
    return {"message": "Boost stopped"}

@app.post("/temporary-charge")
def temporary_charge():
    until = datetime.now() + timedelta(hours=12)
    with open("/tmp/temporary_charge_until", "w") as f:
        f.write(str(int(until.timestamp())))
    if not is_boost_active():
        send_udp_message_and_receive_response("curr 6000")
    send_udp_message_and_receive_response("ena 1")
    return {"message": "Temporary charging at 6000 started", "until": until.isoformat()}

@app.post("/stop-temporary-charge")
def stop_temporary_charge():
    with open("/tmp/temporary_charge_until", "w") as f:
        f.write("0")
    return {"message": "Temporary charging stopped"}
