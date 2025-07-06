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

if __name__ == "__main__":
    hours = get_sun_hours_eichstaett()
    print(f"☀️ Estimated sun hours in next 48 h around Eichstätt: {hours}")
