from fastapi import FastAPI
from datetime import datetime, timedelta
from utils import send_udp_message_and_receive_response

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or limit to ["http://192.168.0.106:3000"] for security
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
    return {"message": "Boost activated", "until": boost_until.isoformat()}


@app.post("/stop-boost")
def stop_boost():
    with open(BOOST_FILE, "w") as f:
        f.write("0")
    send_udp_message_and_receive_response("curr 6000")  # reset to normal current
    return {"message": "Boost stopped"}
