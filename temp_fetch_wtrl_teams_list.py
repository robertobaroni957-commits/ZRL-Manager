import requests
import json
import os

base_url = "https://www.wtrl.racing/api/zrl/"
season_number = 17 # Example season
teams_list_url = f"{base_url}{season_number}/teams/"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.wtrl.racing/",
}

try:
    response = requests.get(teams_list_url, headers=headers, timeout=10)
    response.raise_for_status() # Raise an exception for HTTP errors
    
    data = response.json()
    print(json.dumps(data, indent=2))
    
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
except json.JSONDecodeError:
    print(f"Error decoding JSON response: {response.text}")
