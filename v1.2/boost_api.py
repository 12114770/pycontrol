from fastapi import FastAPI
from datetime import datetime, timedelta
from utils import send_udp_message_and_receive_response, is_boost_active
import requests

from fastapi.middleware.cors import CORSMiddleware
SERVER_IP = "localhost"
VIN = "VR7EZZKXZPJ655855"
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
    return {"message": "Temporary charging at 6000 started", "until": until.isoformat()}

@app.post("/stop-temporary-charge")
def stop_temporary_charge():
    with open("/tmp/temporary_charge_until", "w") as f:
        f.write("0")
    return {"message": "Temporary charging stopped"}


from fastapi.responses import JSONResponse

@app.post("/charge_limit_80")
def set_charge_limit_80():
    url = f"http://{SERVER_IP}:5000/charge_control?vin={VIN}&percentage=80"
    try:
        r = requests.get(url, timeout=5)
        print(f"✅ PSA response: {r.status_code} - {r.text}")
        return JSONResponse(
            status_code=200,
            content={"message": "Charging limit set to 80%"}
        )
    except Exception as e:
        print(f"❌ Error in /charge_limit_80: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/charge_limit_100")
def set_charge_limit_100():
    url = f"http://{SERVER_IP}:5000/charge_control?vin={VIN}&percentage=100"
    try:
        r = requests.get(url)
        return {
            "message": "Charging limit set to 100%"
        }
    except Exception as e:
        print("wrong Vin")
        return {"error": str(e)}
