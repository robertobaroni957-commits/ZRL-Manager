import os
import json
from flask import Blueprint, render_template, flash, redirect, url_for, request
from newZRL import db
from newZRL.models.season import Season
from newZRL.models.round import Round
from newZRL.models.race import Race
import requests
from dateutil import parser

import_wtrl_season_bp = Blueprint(
    'import_wtrl_season', __name__, template_folder='templates'
)

JSON_DIR = r"C:\Progetti\ZRL_MANAGER_V2.0\newZRL\data\races_json"
os.makedirs(JSON_DIR, exist_ok=True)


def parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = parser.isoparse(date_str)
        return dt.date()  # solo data, senza ora
    except Exception as e:
        print(f"[WARN] parse_date fallito per '{date_str}': {e}")
        return None


def fetch_and_save_json(season_name="17"):
    """Scarica solo il round corrente per due categorie rappresentative: A e C"""
    categories = ["A", "C"]  # A rappresenta A+B, C rappresenta C+D
    base_url = "https://www.wtrl.racing/api/wtrlruby/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.wtrl.racing/zwift-racing-league/schedule/{season_name}/r1/",
        "wtrl-api-version": "2.7",
    }

    saved_files = []
    for category in categories:
        params = {
            "wtrlid": "zrl",
            "season": season_name,
            "category": category,
            "action": "schedule",
            "test": "c2NoZWR1bGU=",
        }
        try:
            resp = requests.get(base_url, headers=headers, params=params, timeout=12)
            if resp.status_code != 200:
                print(f"[WARN] Categoria {category}: Status code {resp.status_code}")
                continue
            data = resp.json()
            filename = os.path.join(JSON_DIR, f"schedule_season{season_name}_cat{category}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            saved_files.append(filename)
        except Exception as e:
            print(f"[ERROR] Categoria {category}: {e}")
    return saved_files



def import_json_to_db(season_name="17"):
    """Importa i JSON nel DB creando season, round e race"""
    files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json") and f.startswith(f"schedule_season{season_name}")]
    if not files:
        print(f"[WARN] Nessun file JSON trovato per la stagione {season_name}")
        return

    all_round_dates = []

    for file in files:
        filepath = os.path.join(JSON_DIR, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] File corrotto {file}: {e}")
            continue

        payload = data.get("payload", [])
        for r in payload:
            d = parse_date(r.get("eventDate"))
            if d:
                all_round_dates.append(d)

    if not all_round_dates:
        print(f"[WARN] Nessuna data valida trovata per la stagione {season_name}")
        return

    # Season
    season = Season.query.filter_by(name=season_name).first()
    if not season:
        season = Season(
            name=season_name,
            start_date=min(all_round_dates),
            end_date=max(all_round_dates)
        )
        db.session.add(season)
        db.session.flush()
    else:
        season.start_date = min(all_round_dates)
        season.end_date = max(all_round_dates)

    # Round + Race
    for file in files:
        filepath = os.path.join(JSON_DIR, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] File corrotto {file}: {e}")
            continue

        payload = data.get("payload", [])
        if not payload:
            continue

        filename_parts = os.path.splitext(file)[0].split("_")
        category = filename_parts[2].replace("cat", "")
        round_number = payload[0].get("roundNumber") or 1  # Prendiamo il round corrente
        round_name = f"Round {round_number}"

        round_dates = [parse_date(r.get("eventDate")) for r in payload if parse_date(r.get("eventDate"))]
        if not round_dates:
            continue

        start_date = min(round_dates)
        end_date = max(round_dates)

        # Round: crea o aggiorna
        round_obj = Round.query.filter_by(season_id=season.id, round_number=round_number).first()
        if not round_obj:
            round_obj = Round(
                season_id=season.id,
                round_number=round_number,
                name=round_name,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            db.session.add(round_obj)
            db.session.flush()  # ID generato subito
        else:
            round_obj.start_date = min(round_obj.start_date or start_date, start_date)
            round_obj.end_date = max(round_obj.end_date or end_date, end_date)

        # Race
        for race_data in payload:
            external_id = str(race_data.get("race") or "")
            if not external_id:
                continue

            race_date = parse_date(race_data.get("eventDate"))
            race = Race.query.filter_by(round_id=round_obj.id, category=category, external_id=external_id).first()

            if not race:
                race = Race(
                    round_id=round_obj.id,
                    category=category,
                    external_id=external_id,
                    name=race_data.get("courseName"),
                    race_date=race_date,
                    format=race_data.get("raceFormat"),
                    world=race_data.get("courseWorld"),
                    course=race_data.get("courseFull"),
                    laps=race_data.get("duration"),
                    distance_km=(race_data.get("lapDistanceInMeters") or 0) / 1000,
                    elevation_m=race_data.get("lapAscentInMeters") or 0,
                    rules=race_data.get("rules"),
                    segments=json.dumps(race_data.get("segments", [])),
                    leadin_distance=race_data.get("leadinDistanceInMeters"),
                    leadin_ascent=race_data.get("leadinAscentInMeters"),
                    active=1
                )
                db.session.add(race)
            else:
                race.name = race_data.get("courseName")
                race.race_date = race_date
                race.format = race_data.get("raceFormat")
                race.world = race_data.get("courseWorld")
                race.course = race_data.get("courseFull")
                race.laps = race_data.get("duration")
                race.distance_km = (race_data.get("lapDistanceInMeters") or 0) / 1000
                race.elevation_m = race_data.get("lapAscentInMeters") or 0
                race.rules = race_data.get("rules")
                race.segments = json.dumps(race_data.get("segments", []))
                race.leadin_distance = race_data.get("leadinDistanceInMeters")
                race.leadin_ascent = race_data.get("leadinAscentInMeters")

    try:
        db.session.commit()
        print(f"[OK] Season {season_name} importata correttamente")
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Commit fallito: {e}")


@import_wtrl_season_bp.route("/run_import", methods=["GET"])
def run_import():
    season_name = request.args.get("season_name", "17")
    fetch_and_save_json(season_name)
    import_json_to_db(season_name)
    flash(f"✅ Stagione {season_name} importata con successo", "success")
    return redirect(url_for("import_wtrl_season.import_page"))


@import_wtrl_season_bp.route("/import_page", methods=["GET"])
def import_page():
    seasons = Season.query.order_by(Season.name.desc()).all()
    return render_template("admin/import_wtrl_season.html", seasons=seasons)
