# newZRL/services/report_service.py

from newZRL import db
from newZRL.models import WTRL_Rider, Team, RaceLineup
from sqlalchemy import func

Rider = WTRL_Rider


def get_report_data(report_type, category_filter=None, team_filter=None):
    category_filter = (category_filter or "").upper().strip()
    team_filter = (team_filter or "").strip()

    rows = []
    columns = []
    lineup_per_team = {}
    race_date = None

    # ------------------------------------------------------------
    # RIDERS + RIDERS COMPACT
    # ------------------------------------------------------------
    if report_type in ["riders", "riders_compact"]:

        query = (
            db.session.query(
                Rider.profile_id,
                Rider.name,
                Rider.category,
                Rider.member_status,
                Rider.riderpoints,
                Team.name.label("team_name")
            ).outerjoin(Team, Team.trc == Rider.team_trc)
        )

        if category_filter:
            query = query.filter(Rider.category.ilike(category_filter))
        if team_filter:
            query = query.filter(Team.name.ilike(team_filter))

        rows_raw = query.order_by(Rider.name.asc()).all()

        # Aggregazione
        aggregated = {}
        for r in rows_raw:
            if r.profile_id not in aggregated:
                aggregated[r.profile_id] = {
                    "profile_id": r.profile_id,
                    "name": r.name,
                    "category": r.category,
                    "riderpoints": r.riderpoints,
                    "status": r.member_status,
                    "teams": []
                }
            aggregated[r.profile_id]["teams"].append(r.team_name or "Senza Team")

        rows = []
        max_teams = 0

        for item in aggregated.values():
            team_list = sorted(set(item["teams"]))
            max_teams = max(max_teams, len(team_list))

            row = {
                "profile_id": item["profile_id"],
                "name": item["name"],
                "category": item["category"],
            }

            for i, tname in enumerate(team_list, start=1):
                row[f"Team {i}"] = tname

            if report_type == "riders":
                row["riderpoints"] = item["riderpoints"]
                row["status"] = item["status"]

            rows.append(row)

        base_cols = ["profile_id", "name", "category"]
        team_cols = [f"Team {i}" for i in range(1, max_teams+1)]

        if report_type == "riders_compact":
            columns = base_cols + team_cols
        else:
            columns = base_cols + ["riderpoints", "status"] + team_cols

        return rows, columns, None, None

    # ------------------------------------------------------------
    # TEAMS
    # ------------------------------------------------------------
    if report_type == "teams":
        teams = Team.query.order_by(Team.name).all()
        rows = []
        for t in teams:
            rows.append({
                "team": t.name,
                "category": t.category,
                "n_riders": db.session.query(Rider).filter(Rider.team_trc == t.trc).count(),
                "captain": t.captain_name or ""
            })

        columns = ["team", "category", "n_riders", "captain"]
        return rows, columns, None, None

    # ------------------------------------------------------------
    # TEAM COMPOSITION  (FIXATO)
    # ------------------------------------------------------------
    if report_type == "team_composition":
        teams = Team.query.order_by(Team.name).all()

        for t in teams:
            if team_filter and t.name != team_filter:
                continue

            riders = db.session.query(Rider).filter(Rider.team_trc == t.trc).all()
            team_rows = []

            for r in riders:
                if category_filter and r.category.upper() != category_filter:
                    continue

                team_rows.append({
                    "team_name": t.name,
                    "profile_id": r.profile_id,
                    "category": r.category,
                    "status": r.member_status,
                    "signedup": r.signedup,
                    "riderpoints": r.riderpoints,
                    "captain": t.captain_name or ""
                })

            rows.extend(team_rows)

        columns = ["team_name", "profile_id", "category", "status", "signedup", "riderpoints", "captain"]
        return rows, columns, None, None

    # ------------------------------------------------------------
    # LINEUP  (FIXATO)
    # ------------------------------------------------------------
    if report_type == "lineup":

        # Stessa logica dell'HTML
        race_date = db.session.query(
            func.min(RaceLineup.race_date)
        ).filter(
            RaceLineup.race_date >= func.current_date()
        ).scalar()

        if not race_date:
            return [], ["team", "profile_id", "category", "status", "race_date"], None, None

        query = (
            db.session.query(
                RaceLineup.race_date,
                Rider.profile_id,
                Rider.category,
                Rider.member_status,
                Team.name.label("team_name")
            )
            .join(Rider, RaceLineup.profile_id == Rider.profile_id)
            .outerjoin(Team, Team.trc == Rider.team_trc)
            .filter(RaceLineup.race_date == race_date)
        )

        if category_filter:
            query = query.filter(Rider.category.ilike(category_filter))
        if team_filter:
            query = query.filter(Team.name.ilike(team_filter))

        rows_raw = query.all()

        for r in rows_raw:
            rows.append({
                "team": r.team_name or "Senza Team",
                "profile_id": r.profile_id,
                "category": r.category,
                "status": r.member_status,
                "race_date": r.race_date
            })

        columns = ["team", "profile_id", "category", "status", "race_date"]
        return rows, columns, None, race_date

