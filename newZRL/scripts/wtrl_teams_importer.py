import os
import json
from datetime import datetime
from newZRL import db
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.models.team import Team

# Path dei JSON
JSON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "wtrl_json"))

def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

def normalize_avatar(url):
    if not url:
        return None
    return url

def extract_division_number(division_str):
    if not division_str:
        return None
    parts = division_str.split()
    last = parts[-1]
    digits = ''.join(ch for ch in last if ch.isdigit())
    return int(digits) if digits else None

def import_wtrl_riders():
    if not os.path.isdir(JSON_DIR):
        print(f"[ERROR] JSON_DIR non trovato: {JSON_DIR}")
        return

    for filename in os.listdir(JSON_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(JSON_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Parsing JSON {filename}: {e}")
            continue

        try:
            # ---------------------------
            # TEAM
            # ---------------------------
            meta = data.get("meta", {})
            team_json = meta.get("team", {})
            competition = meta.get("competition", {})

            trc = meta.get("trc") or team_json.get("tttid") or team_json.get("teamid")
            team = Team.query.filter_by(trc=trc).first() if trc else None
            if not team:
                team = Team()
                team.created_at = datetime.utcnow()

            team.name = team_json.get("name")
            team.jerseyimage = team_json.get("jerseyimage")

            # Mappatura corretta basata sul JSON fornito dall'utente:
            # team.category (nel DB) deve essere competition.division (es. 'C')
            # team.division (nel DB) deve essere meta.division (es. 'Open Shamrock League Division C')
            team.category = competition.get("division")
            if not team.category:
                print(f"[WARNING] Categoria non trovata per il team: {team_json.get('name')} (TRC: {trc}). Dati JSON: competition={competition}, meta={meta}")
            team.division = meta.get("division")

            team.division_number = extract_division_number(team.division)
            team.trc = trc
            team.wtrl_team_id = team_json.get("tttid") or team_json.get("teamid") or trc
            team.member_count = meta.get("memberCount")
            team.last_synced_at = datetime.utcnow()
            team.is_active = True if competition.get("status") == "ACTIVE" else False
            team.status = competition.get("status")
            team.updated_at = datetime.utcnow()

            db.session.add(team)
            db.session.flush()  # serve per avere team.id

            # ---------------------------
            # WTRL RIDERS
            # ---------------------------
            riders_list = data.get("riders", [])
            current_wtrl_ids = []

            for r in riders_list:
                zwift_power_id = r.get("tmuid")
                if not zwift_power_id:
                    print(f"[WARN] Rider senza tmuid in {filename}: {r.get('name')}")
                    continue

                # cerca esistente
                rider = WTRL_Rider.query.filter_by(zwift_power_id=zwift_power_id, team_id=team.id).first()
                if not rider:
                    rider = WTRL_Rider.query.filter_by(zwift_power_id=zwift_power_id).first()
                if not rider:
                    rider = WTRL_Rider(zwift_power_id=zwift_power_id)

                rider.team_id = team.id
                rider.name = r.get("name")
                rider.memberStatus = r.get("memberStatus")
                rider.signedup = bool(r.get("signedup", False))
                rider.riderpoints = r.get("riderpoints", 0)
                rider.appearancesRound = r.get("appearancesRound", 0)
                rider.appearancesSeason = r.get("appearancesSeason", 0)
                rider.avatar = normalize_avatar(r.get("avatar"))
                rider.category = r.get("category")
                # statistiche opzionali
                rider.zftp = r.get("zftp")
                rider.zftpw = r.get("zftpw")
                rider.zmap = r.get("zmap")
                rider.zmapw = r.get("zmapw")
                rider.profileId = r.get("profileId")
                rider.userId = r.get("userId")
                rider.joined_at = parse_datetime(r.get("joined_at"))
                rider.last_race_at = parse_datetime(r.get("last_race_at"))

                if getattr(rider, "created_at", None) is None:
                    rider.created_at = datetime.utcnow()
                rider.updated_at = datetime.utcnow()

                db.session.add(rider)
                db.session.flush()
                current_wtrl_ids.append(rider.id)

            # Rimuove rider non più nel JSON
            if current_wtrl_ids:
                WTRL_Rider.query.filter(
                    WTRL_Rider.team_id == team.id,
                    ~WTRL_Rider.id.in_(current_wtrl_ids)
                ).delete(synchronize_session=False)

            db.session.commit()
            print(f"[OK] Importato {filename} -> team id {team.id} riders {len(current_wtrl_ids)}")

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Import file {filename}: {e}")

    print("Import WTRL riders completato.")

if __name__ == "__main__":
    import_wtrl_riders()
