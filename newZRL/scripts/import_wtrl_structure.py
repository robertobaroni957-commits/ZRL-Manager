import json
from newZRL import db
from newZRL.models import WTRLCompetition, WTRLLeague, WTRLDivision, WTRLRace

import os
JSON_FILE = os.path.join(os.path.dirname(__file__), "wtrl_full.json")


def import_wtrl():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    competitions = data["payload"]["competition"]

    for comp in competitions:
        comp_id = int(comp["value"])
        comp_name = comp["text"]

        # Inserisci competition
        c = WTRLCompetition(id=comp_id, name=comp_name)
        db.session.add(c)
        db.session.flush()  # forza il DB a generare l'id se serve

        for league in comp.get("leagues", []):
            league_id = int(league["value"])
            league_name = league["text"]

            l = WTRLLeague(id=league_id, competition_id=comp_id, name=league_name)
            db.session.add(l)
            db.session.flush()

            for division in league.get("divisions", []):
                division_code = division["value"]
                division_text = division["text"]

                d = WTRLDivision(
                    league_id=league_id,
                    code=division_code,
                    name=division_text
                )
                db.session.add(d)
                db.session.flush()  # serve per avere l'id della division

                for race in division.get("races", []):
                    race_number = int(race["value"])
                    race_name = race["text"]
                    race_format = race["format"]

                    r = WTRLRace(
                        division_id=d.id,
                        number=race_number,
                        name=race_name,
                        race_format=race_format
                    )
                    db.session.add(r)

    db.session.commit()
    print("WTRL structure imported successfully!")

if __name__ == "__main__":
    import_wtrl()
