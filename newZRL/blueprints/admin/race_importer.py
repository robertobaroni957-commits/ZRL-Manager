# newZRL/blueprints/admin/race_importer.py

import requests
import time
import random
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
from newZRL import db
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.models.race_results import RaceResultsTeam, RaceResultsRider, RoundStanding

admin_race_bp = Blueprint("admin_race", __name__, url_prefix="/admin/race")

# --------------------------
# CONFIGURAZIONE COOKIE/API
# --------------------------
WTRL_COOKIES = {
    "wtrl_sid": "1540de2fed7d9327906f6c2a591c3ba2",
    "wtrl_ouid": "eyJpYXQiOjE3NjQwODE4MjYsImVhdCI6MTc2NjY3MzgyNiwicHJvZmlsZV9waWMiOiJodHRwczpcL1wvd3d3Lnd0cmwucmFjaW5nXC91cGxvYWRzXC9wcm9maWxlX3BpY3R1cmVcLzE2NDExOTc0NTZfYmVsbGEtdGFydGFydWdhLXN1bGxhLWJpY2ktYWRlc2l2by5qcGciLCJmaXJzdF9uYW1lIjoiUm9iZXJ0byIsImxhc3RfbmFtZSI6IkJhcm9uaSIsImVtYWlsIjoicm9iZXJ0by5iYXJvbmlAbGliZXJvLml0IiwidXNlckNsYXNzIjoiMSIsInp3aWZ0SWQiOiIyOTc1MzYxIiwidXVpZCI6ImM2ZWU4NThiLWRjMGMtNDFiNi04M2JjLThjMzRlNWE0OTQ3MCIsInVzZXJJZCI6IjQ0Nzg1IiwiY291bnRyeV9pZCI6IjM4MCIsImdlbmRlciI6Ik1hbGUiLCJyYWNlVGVhbSI6IjAifQ%3D%3D.1540de2fed7d9327906f6c2a591c3ba2",
}
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------------------
# UTILS
# --------------------------
def normalize_name(s):
    """Normalizza i nomi per confronto robusto."""
    if not s:
        return ""
    s = s.strip().upper()
    # rimuovi prefissi comuni e doppio spazio
    s = s.replace("TEAM ", "").replace("  ", " ")
    return s

def ensure_wtrl_json_ready(season: str, class_id: str, race_number: int,
                           max_retries: int = 12, initial_delay: float = 1.5,
                           max_delay: float = 6.0):
    """
    Chiede l'endpoint WTRL e attende che ritorni 200.
    Ritorna (success, response) dove response è l'oggetto requests.Response (se success)
    o l'ultima Response / errore se fallisce.
    Usa exponential backoff + jitter per non stressare il server.
    """
    url = f"https://www.wtrl.racing/api/zrl/results/{season}/{class_id}/{race_number}"
    delay = initial_delay

    last_response = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, cookies=WTRL_COOKIES, timeout=20)
        except Exception as e:
            # rete/timeout: loggalo e ritenta
            print(f"[ensure_wtrl_json_ready] attempt {attempt} network error: {e}")
            last_response = None
            # backoff with jitter
            time.sleep(min(max_delay, delay) + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.8)
            continue

        last_response = resp

        if resp.status_code == 200:
            # JSON pronto
            return True, resp

        if resp.status_code == 202:
            # Non pronto: aspetta e ritenta
            print(f"[ensure_wtrl_json_ready] attempt {attempt} got 202 (not ready). Waiting {delay:.1f}s")
            time.sleep(min(max_delay, delay) + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.8)
            continue

        # Qualsiasi altro codice (403, 404, 500...) -> fallimento
        print(f"[ensure_wtrl_json_ready] attempt {attempt} got HTTP {resp.status_code}")
        # se è HTML di redirect (login), lo mostriamo per debug
        print(resp.text[:800])
        return False, resp

    # Se abbiamo esaurito i retry
    return False, last_response


# --------------------------
# ROUTE IMPORT GARA
# --------------------------
@admin_race_bp.route("/import", methods=["GET", "POST"])
@login_required
def import_race():
    if request.method == "POST":

        race_number = request.form.get("race_number")
        if not race_number or not race_number.isdigit():
            flash("Numero gara non valido", "error")
            return redirect(url_for("admin_race.import_race"))
        race_number = int(race_number)

        # Carica tutti i team con competition_class e competition_season
        teams = Team.query.filter(
            Team.competition_class.isnot(None),
            Team.competition_season.isnot(None)
        ).all()

        total_teams = len(teams)
        processed = 0

        for team in teams:
            season = team.competition_season
            class_id = team.competition_class

            # Step 1: assicurati che il JSON venga generato (retry su 202)
            ok, response = ensure_wtrl_json_ready(season, class_id, race_number,
                                                 max_retries=14, initial_delay=1.2, max_delay=8.0)

            if not ok:
                # response potrebbe essere None o una Response non-200
                status = response.status_code if response is not None else "N/A"
                flash(f"Team {team.name}: impossibile ottenere JSON WTRL (HTTP {status})", "error")
                # mostriamo un estratto della risposta per debugging se presente
                if response is not None:
                    print(f"[import_race] RAW for {team.name} (status {response.status_code}):")
                    print(response.text[:800])
                continue

            # Step 2: parse JSON (ora response dovrebbe essere 200)
            try:
                data = response.json()
            except ValueError:
                flash(f"Team {team.name}: risposta non JSON ricevuta anche dopo 200", "error")
                print(response.text[:1000])
                continue

            if "payload" not in data or not isinstance(data["payload"], list):
                flash(f"Team {team.name}: payload mancante o non array", "error")
                print("RAW payload:", data)
                continue

            payload = data["payload"]

            # Step 3: cerca il team nel payload con matching robusto
            team_payload = None
            db_name = normalize_name(team.name)

            for entry in payload:
                json_name = normalize_name(entry.get("teamname") or "")

                # match perfetto
                if json_name == db_name:
                    team_payload = entry
                    break

                # match parziale (db name incluso in json_name)
                if db_name and db_name in json_name:
                    team_payload = entry
                    break

                # fallback su id1 / id5 (possono essere int o string)
                id1 = entry.get("id1")
                id5 = entry.get("id5")
                try:
                    if id1 is not None and str(id1) == str(team.trc):
                        team_payload = entry
                        break
                except Exception:
                    pass
                try:
                    if id5 is not None and str(id5) == str(team.trc):
                        team_payload = entry
                        break
                except Exception:
                    pass

            if not team_payload:
                flash(f"Team {team.name}: non trovato nel JSON WTRL (season={season} class={class_id})", "warning")
                # per debugging, puoi uncommentare:
                # print("PAYLOAD SAMPLE:", payload[:5])
                continue

            # Ignora placeholder / team senza risultati (es. timeResult == "0.000")
            time_result = team_payload.get("timeResult") or "0"
            if str(time_result).strip() in ("0", "0.000"):
                flash(f"Team {team.name}: risultato vuoto (timeResult={time_result}) — salto", "warning")
                continue

            # ----------------------
            # CREA RaceResultsTeam
            # ----------------------
            try:
                rrt = RaceResultsTeam(
                    season=int(season),
                    class_id=class_id,
                    race=race_number,
                    team_id=team.trc,
                    finp=int(team_payload.get("finp", 0)),
                    pbp=int(team_payload.get("pbp", 0)),
                    totp=int(team_payload.get("totp", 0)),
                    falp=int(team_payload.get("falp", 0)),
                    ftsp=int(team_payload.get("ftsp", 0)),
                    time_result=team_payload.get("timeResult"),
                    distance_result=team_payload.get("distanceResult")
                )
                db.session.add(rrt)
                db.session.flush()  # per avere rrt.id
            except Exception as e:
                db.session.rollback()
                flash(f"Team {team.name}: errore creando RaceResultsTeam -> {e}", "error")
                print("ERR create rrt:", e)
                continue

            # ----------------------
            # CREA RaceResultsRider
            # ----------------------
            members = team_payload.get("a", []) or []
            for member in members:
                # zid è preferibile, ma il JSON a volte usa p1
                rider_id = member.get("zid") or member.get("p1") or ""
                rider_id = str(rider_id)

                if not rider_id or rider_id in ("0", "None"):
                    # skip entry senza id valido
                    continue

                rider = WTRL_Rider.query.filter_by(id=rider_id).first()
                if not rider:
                    # se non esiste il rider in WTRL_Rider, possiamo anche loggare per import futuro
                    print(f"[import_race] Rider non trovato in WTRL_Rider: rider_id={rider_id}, team={team.name}")
                    continue

                try:
                    rrr = RaceResultsRider(
                        race_team_result_id=rrt.id,
                        rider_id=rider.id,
                        finp=int(member.get("finrp", 0)),
                        pbp=int(member.get("pbprp", 0)),
                        totp=int(member.get("totrp", 0)),
                        falp=int(member.get("falrp", 0)),
                        ftsp=int(member.get("ftsrp", 0)),
                        time_result=member.get("timeResult"),
                        distance_result=member.get("distanceResult"),
                        wkg=float(member.get("wkg") or 0),
                        watts=float(member.get("watts") or 0),
                        gap=str(member.get("gap") or "0")
                    )
                    db.session.add(rrr)
                except Exception as e:
                    print(f"[import_race] errore creando RaceResultsRider per rider {rider_id}: {e}")
                    # non rollback completo, continuiamo con gli altri riders

            # commit per team
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Team {team.name}: errore commit DB -> {e}", "error")
                print("ERR commit:", e)
                continue

            # ----------------------
            # AGGIORNA RoundStanding
            # ----------------------
            try:
                rs = RoundStanding.query.filter_by(
                    season=int(season),
                    class_id=class_id,
                    team_id=team.trc
                ).first()

                if not rs:
                    rs = RoundStanding(
                        season=int(season),
                        class_id=class_id,
                        team_id=team.trc,
                        total_points=rrt.totp
                    )
                    db.session.add(rs)
                else:
                    rs.total_points += rrt.totp
                    rs.updated_at = datetime.utcnow()

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"[import_race] errore aggiornando RoundStanding per team {team.name}: {e}")

            processed += 1
            flash(f"Team {team.name} importato ({processed}/{total_teams})", "success")

            # Sleep breve per non sovraccaricare WTRL
            time.sleep(0.9)

        flash("Importazione completata!", "success")
        return redirect(url_for("admin_race.import_race"))

    # GET -> mostra form
    return render_template("admin/import_race_result.html")
