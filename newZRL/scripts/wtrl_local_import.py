import json
from pathlib import Path
from newZRL import create_app, db
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider

# 📂 Path alla cartella dei JSON
DATA_DIR = Path(__file__).parent.parent / "data" / "wtrl_json"

def load_team_files():
    """Carica tutti i file team_XXXXX.json"""
    if not DATA_DIR.exists():
        print(f"Cartella {DATA_DIR} non trovata!")
        return []

    json_files = sorted(DATA_DIR.glob("team_*.json"))
    return json_files


def import_team(json_data):
    """Importa un singolo team"""
    meta = json_data["meta"]

    trc = meta["trc"]
    team = Team.query.filter_by(trc=trc).first()

    if not team:
        team = Team(trc=trc)
        db.session.add(team)

    # --- Campi team ---
    team.name = meta.get("team", {}).get("name")
    team.division = meta.get("division")
    team.jerseyimage = meta.get("team", {}).get("jerseyimage")
    team.member_count = meta.get("memberCount", 0)

    captain = meta.get("administrators", {}).get("captain")
    if captain:
        team.captain_profile_id = captain.get("profileId")

    db.session.flush()  # necessario per ottenere team.id

    return team


def import_riders(team, json_data):
    """Importa i rider per un team"""
    riders_json = json_data.get("riders", [])
    current_ids = []

    for r in riders_json:
        zwid = r.get("profileId")   # questo è il vero ID identificativo

        # 🔍 cerca per team + zwift_power_id
        wr = WTRL_Rider.query.filter_by(
            team_id=team.id,
            zwift_power_id=zwid
        ).first()

        if not wr:
            wr = WTRL_Rider(
                team_id=team.id,
                zwift_power_id=zwid
            )
            db.session.add(wr)

        # --- Campi rider ---
        wr.memberStatus = r.get("memberStatus")
        wr.signedup = r.get("signedup", False)
        wr.riderpoints = r.get("riderpoints", 0)
        wr.appearancesRound = r.get("appearancesRound")
        wr.appearancesSeason = r.get("appearancesSeason")
        wr.avatar = r.get("avatar")
        wr.category = r.get("category")

        db.session.flush()
        current_ids.append(wr.id)

    # 🔥 Elimina i rider non più presenti
    if current_ids:
        WTRL_Rider.query.filter(
            WTRL_Rider.team_id == team.id,
            ~WTRL_Rider.id.in_(current_ids)
        ).delete(synchronize_session=False)

    return len(riders_json)


def run_import():
    """Import locale da JSON"""
    app = create_app()

    with app.app_context():
        json_files = load_team_files()
        if not json_files:
            print("Nessun file JSON trovato!")
            return

        print(f"Trovati {len(json_files)} file.")

        for f in json_files:
            print(f"\n➡ Import {f.name}")

            with f.open("r", encoding="utf-8") as fp:
                data = json.load(fp)

            team = import_team(data)
            count = import_riders(team, data)

            print(f"   ✓ Team {team.name} ({team.trc}) importato")
            print(f"   ✓ Riders importati: {count}")

        db.session.commit()
        print("\n🎉 IMPORT COMPLETATO CON SUCCESSO!")


if __name__ == "__main__":
    run_import()
