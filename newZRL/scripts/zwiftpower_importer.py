# newZRL/scripts/zwiftpower_importer.py
import requests
import json
from flask import current_app
from newZRL import db
from newZRL.models import Rider

COOKIE = (
    "phpbb3_lswlk_k=; "
    "phpbb3_lswlk_u=275700; "
    "phpbb3_lswlk_sid=8212abfd5df30f32451900443cc2838a; "
    "CloudFront-Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly96d2lmdHBvd2VyLmNvbS8qIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoyMTQ3NDgzNjQ3fX19XX0_; "
    "CloudFront-Signature=7f6sOCtlQZRe90rpvVq9l84rRNbxl4HBsyEqJByfkMsXWzVe2JkpWGGMZ~KZ1W5w9lm~wYTaQM8ZHFO-MCBokO9EsyeeAcxFOd7gIu5OTcFFFankW4L6RBR-o3oS48dIi22zpWjLZAyku4SXlXbhtMUJrLsASioVG~UDe00Kvc3OWw~WAf0a8LkrdMxG4kIOlb7vvKYEKONo7IO5-JxNVq5WDwMJqB43qRrI2dSK3TMDUsugJHd6QmWpaPxQPHDxrH7MkuBaumdUS1138NbwLL8KwVfcLlV~VnooURL~ID~9lLQHfQ11tkASNzeJgYczkBXTGiKeOh9npbElvqlfOg__; "
    "CloudFront-Key-Pair-Id=K2HE75OK1CK137"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://zwiftpower.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": COOKIE,
}

TEAM_URL = "https://zwiftpower.com/api3.php?do=team_riders&id=16461"


def scrape_team():
    """Scarica i membri del team INOX da ZwiftPower API."""
    r = requests.get(TEAM_URL, headers=HEADERS)
    data = json.loads(r.text)

    riders = data.get("data", [])
    parsed = []

    for r in riders:
        parsed.append({
            "zwift_power_id": r.get("zwid"),
            "name": r.get("name"),
            "country": r.get("flag"),
            "age": r.get("age"),
            "weight": r.get("w"),
            "ftp": r.get("ftp"),
            "ce_category": r.get("div"),
            "ce_category_women": r.get("divw"),
            "races": r.get("r"),
            "strava_profile": r.get("aid"),
            "zp_rank": r.get("rank"),
            "zp_skill": r.get("skill"),
            "zp_skill_race": r.get("skill_race"),
            "zp_skill_seg": r.get("skill_seg"),
            "zp_skill_power": r.get("skill_power"),
            "total_distance": r.get("distance"),
            "total_climbed": r.get("climbed"),
            "total_energy": r.get("energy"),
            "total_time": r.get("time"),
            "email": r.get("email"),
            "watt_20min": r.get("h_1200_w"),
            "wkg_20min": r.get("h_1200_wkg"),
            "watt_15sec": r.get("h_15_watt"),
            "wkg_15sec": r.get("h_15_wkg"),
        })

    return parsed


def import_members_to_db(members):
    """Importa o aggiorna rider nel DB."""
    new = 0
    updated = 0

    for m in members:
        rid = Rider.query.filter_by(zwift_power_id=m["zwift_power_id"]).first()

        if not rid:
            rid = Rider(zwift_power_id=m["zwift_power_id"])
            new += 1
        else:
            updated += 1

        for key, value in m.items():
            if hasattr(rid, key):
                setattr(rid, key, value)

        db.session.add(rid)

    db.session.commit()

    return {"new": new, "updated": updated}
