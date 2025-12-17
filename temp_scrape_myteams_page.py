import requests
import re
import json
import os

myteams_url = "https://www.wtrl.racing/zwift-racing-league/myteams/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.wtrl.racing/",
}

try:
    response = requests.get(myteams_url, headers=headers, timeout=10)
    response.raise_for_status() # Raise an exception for HTTP errors
    
    html_content = response.text
    
    # Attempt to find team IDs using regex.
    # The IDs appear in the URL structure like /api/zrl/17/teams/XXXXX
    # Or in the HTML itself within data attributes or similar.
    # Let's look for "teams/" followed by 5 or more digits.
    team_id_pattern = re.compile(r'/api/zrl/\d+/teams/(\d{5,})')
    found_team_ids = set(team_id_pattern.findall(html_content))
    
    if found_team_ids:
        print(f"Found Team IDs: {list(found_team_ids)}")
    else:
        print("No Team IDs found on the page.")
        
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
