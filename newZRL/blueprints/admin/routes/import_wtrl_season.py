import os
import json
from flask import render_template, flash, redirect, url_for, request
from newZRL import db
from newZRL.models.season import Season
from newZRL.models.round import Round
from newZRL.models.race import Race
import requests
from dateutil import parser

from ..bp import admin_bp


def parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = parser.isoparse(date_str)
        return dt.date()  # solo data, senza ora
    except Exception as e:
        print(f"[WARN] parse_date fallito per '{date_str}': {e}")
        return None


def fetch_wtrl_schedule_data(season_name="17", categories=None):
    """Fetches race schedule data directly from WTRL API for specified categories."""
    if categories is None:
        categories = ["A", "B", "C", "D"] # Default to all categories
    
    base_url = "https://www.wtrl.racing/api/wtrlruby/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.wtrl.racing/zwift-racing-league/schedule/{season_name}/r1/",
        "wtrl-api-version": "2.7",
    }

    all_payloads = []
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
            # If the JSON contains all categories, we only need the payload
            # Otherwise, if it's filtered by category, append its payload
            if "payload" in data:
                all_payloads.extend(data["payload"])
        except Exception as e:
            print(f"[ERROR] Categoria {category}: {e}")
    return all_payloads



def import_wtrl_schedule_data_to_db(season_name="17", all_race_payloads=None):
    """Imports WTRL race schedule data directly into the DB creating season, round, and race entries."""
    if all_race_payloads is None:
        all_race_payloads = [] # Ensure it's a list

    if not all_race_payloads:
        print(f"[WARN] Nessun payload di gara fornito per la stagione {season_name}")
        return

    # Extract all round dates from all race payloads for season date calculation
    all_round_dates = []
    for race_data in all_race_payloads:
        d = parse_date(race_data.get("eventDate"))
        if d:
            all_round_dates.append(d)

    if not all_round_dates:
        print(f"[WARN] Nessuna data valida trovata per la stagione {season_name} nel payload fornito")
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
        season.start_date = min(season.start_date or min(all_round_dates), min(all_round_dates))
        season.end_date = max(season.end_date or max(all_round_dates), max(all_round_dates))

    # Aggregate all race data by round number to ensure each round is processed once
    races_by_round = {}
    for race_data in all_race_payloads:
        round_number = race_data.get("roundNumber") or 1
        if round_number not in races_by_round:
            races_by_round[round_number] = []
        races_by_round[round_number].append(race_data)

    for round_number, races_in_round in races_by_round.items():
        round_name = f"Round {round_number}"

        round_dates = [parse_date(r.get("eventDate")) for r in races_in_round if parse_date(r.get("eventDate"))]
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
            db.session.flush()
        else:
            round_obj.start_date = min(round_obj.start_date or start_date, start_date)
            round_obj.end_date = max(round_obj.end_date or end_date, end_date)

        # Race
        for race_data in races_in_round:
            external_id = str(race_data.get("race") or "")
            if not external_id:
                continue

            race_date = parse_date(race_data.get("eventDate"))
            category = race_data.get("subgroup_label") 
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
                    tags=json.dumps(race_data.get("tags", [])),
                    pace_type=race_data.get("paceType"),
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
                race.tags = json.dumps(race_data.get("tags", []))
                race.pace_type = race_data.get("paceType")
                race.category = category # Ensure this is still correctly assigned

    try:
        db.session.commit()
        print(f"[OK] Season {season_name} importata correttamente")
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Commit fallito: {e}")


@admin_bp.route("/run_import", methods=["GET"])
def run_import():
    season_name = request.args.get("season_name", "17")
    
    # Fetch data directly from WTRL API
    all_race_payloads = fetch_wtrl_schedule_data(season_name)
    
    # Import fetched data into DB
    import_wtrl_schedule_data_to_db(season_name, all_race_payloads)
    
    flash(f"✅ Stagione {season_name} importata con successo", "success")
    return redirect(url_for("admin_bp.import_page"))


@admin_bp.route("/import_page", methods=["GET"])
def import_page():
    seasons = Season.query.order_by(Season.name.desc()).all()
    return render_template("admin/import_wtrl_season.html", seasons=seasons)
