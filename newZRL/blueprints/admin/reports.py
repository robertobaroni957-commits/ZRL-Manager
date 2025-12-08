from flask import Blueprint, request, render_template, flash
from flask_login import login_required
from newZRL import db
from newZRL.models import Team, WTRL_Rider, RaceLineup
from newZRL.models.race_results import RaceResultsTeam, RoundStanding
from sqlalchemy import func

Rider = WTRL_Rider
admin_reports_bp = Blueprint("admin_reports", __name__, url_prefix="/admin/reports")


@admin_reports_bp.route("/")
@login_required
def index():
    # ---------------------------
    # Filtri GET
    # ---------------------------
    report_type = request.args.get("report_type", "riders_compact").strip()
    category_filter = (request.args.get("category") or "").strip().upper()
    team_filter_raw = (request.args.get("team") or "").strip()

    if category_filter in ["", "TUTTI", "TUTTE", "ALL"]:
        category_filter = None
    if team_filter_raw.upper() in ["", "TUTTI", "ALL"]:
        team_filter_raw = None

    valid_reports = [
        "riders_compact", "riders", "teams", "lineup",
        "team_composition", "round_standings"
    ]
    if report_type not in valid_reports:
        flash("Tipo di report non valido", "danger")
        report_type = "riders_compact"

    # ---------------------------
    # Lista categorie disponibili dai team
    # ---------------------------
    categories = [c[0] for c in db.session.query(Team.category)
                  .distinct()
                  .order_by(Team.category.asc())
                  .all() if c[0]]

    # ---------------------------
    # Filtra i team per categoria e nome
    # ---------------------------
    team_query = Team.query
    if category_filter:
        team_query = team_query.filter(func.upper(Team.category) == category_filter)
    if team_filter_raw:
        team_query = team_query.filter(
            (Team.trc.ilike(team_filter_raw)) | (Team.name.ilike(f"%{team_filter_raw}%"))
        )
    teams_all = team_query.order_by(Team.name.asc()).all()
    teams_list = [t.name for t in teams_all]

    # ---------------------------
    # Risolvi TRC per filtro team
    # ---------------------------
    team_filter_trc = None
    if team_filter_raw:
        t_match = next(
            (t for t in teams_all if t.name.lower() == team_filter_raw.lower() or str(t.trc).lower() == team_filter_raw.lower()),
            None
        )
        if t_match:
            team_filter_trc = t_match.trc

    rows, columns, lineup_per_team, race_date = [], [], {}, None

    # ---------------------------
    # Riders / Riders Compact
    # ---------------------------
    if report_type in ["riders", "riders_compact"]:
        query = db.session.query(
            Rider.profile_id,
            Rider.name,
            Rider.member_status,
            Rider.riderpoints,
            Rider.team_trc,
            Team.name.label("team_name"),
            Team.category.label("team_category")
        ).outerjoin(Team, Team.trc == Rider.team_trc)

        # Applica filtro team
        if team_filter_trc:
            query = query.filter(Rider.team_trc == team_filter_trc)
        elif team_filter_raw:
            query = query.filter(Team.name.ilike(f"%{team_filter_raw}%"))

        # Applica filtro categoria (team)
        if category_filter:
            query = query.filter(func.upper(Team.category) == category_filter)

        rows_raw = query.order_by(Rider.name.asc()).all()

        # Aggregazione team
        aggregated_riders = {}
        for r in rows_raw:
            profile_id = r.profile_id
            team_name = r.team_name or "Senza Team"

            if profile_id not in aggregated_riders:
                aggregated_riders[profile_id] = {
                    "profile_id": r.profile_id,
                    "name": r.name,
                    "riderpoints": r.riderpoints,
                    "member_status": r.member_status,
                    "teams": []
                }
            aggregated_riders[profile_id]["teams"].append(team_name)

        rows = []
        max_teams = 0
        for data in aggregated_riders.values():
            team_names = sorted(set(data["teams"]))
            max_teams = max(max_teams, len(team_names))

            row = {"profile_id": data["profile_id"], "name": data["name"]}
            for i, team_name in enumerate(team_names):
                row[f"Team {i+1}"] = team_name
            if report_type == "riders":
                row["riderpoints"] = data["riderpoints"]
                row["status"] = data["member_status"]

            rows.append(row)

        base_columns = ["profile_id", "name"]
        team_columns = [f"Team {i+1}" for i in range(max_teams)]
        columns = base_columns + (team_columns if report_type == "riders_compact" else ["riderpoints", "status"] + team_columns)

    # ---------------------------
    # Teams
    # ---------------------------
    elif report_type == "teams":
        rows = []
        for t in teams_all:
            n_riders = db.session.query(Rider).filter(Rider.team_trc == t.trc).count()
            rows.append({
                "team": t.name,
                "category": t.category,
                "n_riders": n_riders,
                "captain": t.captain_name or ""
            })
        columns = ["team", "category", "n_riders", "captain"]

    # ---------------------------
    # Team Composition / Lineup
    # ---------------------------
    elif report_type in ["team_composition", "lineup"]:
        lineup_dict = {}

        if report_type == "team_composition":
            for t in teams_all:
                riders = WTRL_Rider.query.filter(WTRL_Rider.team_trc == t.trc)\
                                         .order_by(WTRL_Rider.profile_id.asc()).all()
                if not riders:
                    continue
                lineup_dict[t.name] = []
                for r in riders:
                    lineup_dict[t.name].append({
                        "profile_id": r.profile_id,
                        "category": t.category or "OTHER",
                        "status": r.member_status or "N/A",
                        "signedup": getattr(r, "signedup", ""),
                        "riderpoints": r.riderpoints,
                        "captain": t.captain_name or ""
                    })
            columns = ["team_name", "profile_id", "category", "status", "signedup", "riderpoints", "captain"]

        elif report_type == "lineup":
            race_date = db.session.query(func.min(RaceLineup.race_date))\
                                  .filter(RaceLineup.race_date >= func.current_date()).scalar()
            if not race_date:
                return "Nessuna gara futura", 400

            query = db.session.query(
                RaceLineup.race_date,
                WTRL_Rider.profile_id,
                WTRL_Rider.name.label("rider_name"),
                Team.name.label("team_name"),
                Team.category.label("team_category")
            ).join(WTRL_Rider, RaceLineup.profile_id == WTRL_Rider.profile_id)\
             .outerjoin(Team, Team.trc == WTRL_Rider.team_trc)\
             .filter(RaceLineup.race_date == race_date)

            if team_filter_trc:
                query = query.filter(WTRL_Rider.team_trc == team_filter_trc)
            elif team_filter_raw:
                query = query.filter(Team.name.ilike(f"%{team_filter_raw}%"))
            if category_filter:
                query = query.filter(func.upper(Team.category) == category_filter)

            rows_raw = query.all()
            lineup_per_team = {}
            for r in rows_raw:
                team = r.team_name or "Senza Team"
                lineup_per_team.setdefault(team, []).append({
                    "profile_id": r.profile_id,
                    "rider_name": r.rider_name,
                    "category": r.team_category or "OTHER",
                    "race_date": r.race_date
                })
            columns = ["team", "profile_id", "rider_name", "category", "race_date"]

    # ---------------------------
    # Round Standings
    # ---------------------------
    elif report_type == "round_standings":
        # Seleziona tutti i round disponibili
        seasons_classes = db.session.query(
            RoundStanding.season,
            RoundStanding.class_id
        ).distinct().order_by(RoundStanding.season.desc()).all()

        standings_rows = []

        for sc in seasons_classes:
            season = sc.season
            class_id = sc.class_id
            standings = (
                RoundStanding.query
                .filter_by(season=season, class_id=class_id)
                .order_by(RoundStanding.total_points.desc())
                .all()
            )
            for idx, s in enumerate(standings, start=1):
                team = Team.query.get(s.team_id)
                standings_rows.append({
                    "season": season,
                    "class_id": class_id,
                    "position": idx,
                    "team": team.name if team else "N/A",
                    "points": s.total_points
                })

        rows = standings_rows
        columns = ["season", "class_id", "position", "team", "points"]

    # ---------------------------
    # Badge colors
    # ---------------------------
    BADGE_COLORS = {
        "A": "#dc3545",
        "B": "#28a745",
        "C": "#17a2b8",
        "D": "#ffc107",
        "OTHER": "#6c757d"
    }

    team_categories = {t.name: t.category for t in teams_all}

    # ---------------------------
    # Round Standings (Classifica punti team)
    # ---------------------------
    if report_type == "round_standings":
        rows = []
        query = db.session.query(
            RoundStanding.season,
            RoundStanding.class_id,
            Team.name.label("team_name"),
            Team.category.label("team_category"),
            RoundStanding.total_points
        ).join(Team, Team.trc == RoundStanding.team_id)

        # Filtri
        if category_filter:
            query = query.filter(func.upper(Team.category) == category_filter)
        if team_filter_trc:
            query = query.filter(RoundStanding.team_id == team_filter_trc)
        elif team_filter_raw:
            query = query.filter(Team.name.ilike(f"%{team_filter_raw}%"))

        rows = query.order_by(RoundStanding.total_points.desc()).all()
        columns = ["season", "class_id", "team_name", "team_category", "total_points"]


    return render_template(
        "admin/reports/index.html",
        report_type=report_type,
        rows=rows,
        columns=columns,
        categories=categories,
        teams=teams_list,
        category_filter=category_filter,
        team_filter=team_filter_raw,
        lineup_per_team=lineup_dict if report_type == "team_composition" else lineup_per_team if report_type == "lineup" else None,
        race_date=race_date,
        team_categories=team_categories
    )
