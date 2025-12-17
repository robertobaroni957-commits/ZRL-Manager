import os
import sys
import csv
import re
import time
from datetime import datetime
from flask import Blueprint, jsonify
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Aggiunge la root del progetto al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from newZRL import create_app

zwift_bp = Blueprint("zwift", __name__)
INOX_TEAM_ID = 16461


def parse_number(value):
    if not value:
        return None
    value = str(value).replace(",", ".").strip()
    try:
        return round(float(re.search(r"[\d.]+", value).group()), 1)
    except:
        return None


def parse_wcell(td):
    if td is None:
        return None
    try:
        text = td.get_text(strip=True)
        match = re.search(r"[\d]+(?:[.,]\d+)?", text)
        return round(float(match.group().replace(",", ".")), 1) if match else None
    except:
        return None


def scrape_profile(driver, zwift_id):
    url = f"https://zwiftpower.com/profile.php?z={zwift_id}"
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    def extract_text(label):
        cell = soup.find("td", string=re.compile(label, re.IGNORECASE))
        return cell.find_next_sibling("td").get_text(strip=True) if cell else None

    def extract_number(label):
        value = extract_text(label)
        return parse_number(value)

    def extract_power_blocks():
        blocks = soup.find_all("div", class_="profile_power_block")
        wkg = []
        watts = []
        for block in blocks:
            text = block.get_text(strip=True)
            wkg_match = re.search(r"([\d.]+)\s*wkg", text)
            watt_match = re.search(r"([\d.]+)\s*watt", text)
            if wkg_match:
                wkg.append(float(wkg_match.group(1)))
            if watt_match:
                watts.append(int(float(watt_match.group(1))))
        return wkg, watts

    profile_data = {
        "race_ranking": extract_number("Race Ranking"),
        "race_ranking_pos": extract_text("Race Ranking"),
        "category": extract_text("Category"),
        "zwift_racing_score": extract_number("Zwift Racing Score"),
        "zpoints": extract_number("ZPoints"),
        "zpoints_pos": extract_text("ZPoints"),
        "country": extract_text("Country"),
        "team": extract_text("Team"),
        "zftp": extract_number("zFTP"),
        "weight": extract_number("Weight"),
        "age": extract_text("Age"),
    }

    wkg_list, watt_list = extract_power_blocks()
    if len(wkg_list) == 4:
        profile_data.update({
            "wkg_15sec": wkg_list[0],
            "wkg_1min": wkg_list[1],
            "wkg_5min": wkg_list[2],
            "wkg_20min": wkg_list[3],
        })
    if len(watt_list) == 4:
        profile_data.update({
            "watt_15sec": watt_list[0],
            "watt_1min": watt_list[1],
            "watt_5min": watt_list[2],
            "watt_20min": watt_list[3],
        })

    return profile_data


def scrape_and_export():
    try:
        options = Options()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        TEAM_URL = f"https://zwiftpower.com/team.php?id={INOX_TEAM_ID}"
        driver.get(TEAM_URL)
        input("➡️ Fai login manuale nella finestra Chrome, poi premi INVIO qui per iniziare lo scraping...")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table#team_riders tbody tr")
        print(f"🔍 Trovate {len(rows)} righe.")

        riders = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            name = cols[2].get_text(strip=True)
            profile_tag = cols[2].find("a")
            profile_url = profile_tag["href"] if profile_tag else ""
            match = re.search(r"[?&](z|user|m)=(\d+)", profile_url)
            zwift_id = int(match.group(2)) if match else None
            if not zwift_id:
                continue

            rider = {
                "zwift_power_id": zwift_id,
                "name": name,
                "category": cols[0].get_text(strip=True),
                "ranking": parse_number(cols[1].get_text(strip=True)),
                "wkg_20min": parse_wcell(cols[3]),
                "watt_20min": parse_wcell(cols[4]),
                "wkg_15sec": parse_wcell(cols[5]),
                "watt_15sec": parse_wcell(cols[6]),
                "profile_url": profile_url,
            }

            profile_data = scrape_profile(driver, zwift_id)
            rider.update(profile_data)
            riders.append(rider)

        driver.quit()

        # ✅ Salvataggio CSV con timestamp
        os.makedirs("exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/zwift_team_export_{timestamp}.csv"
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=riders[0].keys())
            writer.writeheader()
            writer.writerows(riders)

        print(f"✅ Scraping completato. File salvato in: {filename}")
        return filename

    except Exception as e:
        print("❌ Errore:", str(e))


# ✅ Esecuzione diretta da terminale o VS Code
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        scrape_and_export()
