import requests
import json
import time

def test_api():
    url = "http://localhost:8002/predict-severity"
    
    # Wait for server to be ready
    time.sleep(2)

    print("--- Testing API with Scenarios ---")

    # Scenario 1: Minor fender bender
    # Daytime, clear weather, low impact, no rollover, seatbelt used
    minor_scenario = {
        "latitude": 28.6139, # Example: New Delhi
        "longitude": 77.2090,
        "hour": 14,
        "lgt_cond": 1,      # Daylight
        "weather": 1,       # Clear
        "vsurcond": 1,      # Dry
        "man_coll": 1,      # Front-to-rear (rear-end)
        "harm_ev": 12,      # Motor vehicle in transport
        "ve_total": 2,
        "body_typ": 4,      # 4-door sedan
        "impact1": 12,      # 12 o'clock (front)
        "rollover": 0,      # No rollover
        "age": 30,
        "seat_pos": 11,     # Driver
        "rest_use": 3       # Shoulder and lap belt used
    }
    
    print("\nScenario 1: Minor Fender Bender (Daylight, Seatbelt, Low Impact)")
    try:
        response = requests.post(url, json=minor_scenario)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Failed to connect: {e}")

    # Scenario 2: Critical Crash
    # Nighttime, raining, rollover, not wearing seatbelt
    critical_scenario = {
        "latitude": 19.0760, # Example: Mumbai
        "longitude": 72.8777,
        "hour": 2,          # 2 AM
        "lgt_cond": 3,      # Dark, unlit
        "weather": 2,       # Rain
        "vsurcond": 2,      # Wet
        "man_coll": 2,      # Head-on
        "harm_ev": 1,       # Rollover/Overturn
        "ve_total": 1,
        "body_typ": 14,     # Compact SUV
        "impact1": 12,      # Front
        "rollover": 1,      # Rollover occurred
        "age": 25,
        "seat_pos": 11,     # Driver
        "rest_use": 7       # None used / Not strapped in
    }

    print("\nScenario 2: Severe Crash (Night, Rain, Rollover, No Seatbelt, Head-on)")
    try:
        response = requests.post(url, json=critical_scenario)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_api()
