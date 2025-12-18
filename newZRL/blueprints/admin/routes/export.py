# export.py
import io
from flask import request, send_file, render_template
from flask_login import login_required
from newZRL import db
from newZRL.models import WTRL_Rider, Team, RaceLineup
from sqlalchemy import func

# ReportLab per PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from ..bp import admin_bp


# ---- Helper: filter options
def get_filter_options():
    all_teams = [t.name for t in Team.query.order_by(Team.name).all()]
    all_categories = sorted([
        c[0] for c in db.session.query(Team.category)
            .distinct()
            .filter(Team.category.isnot(None))
            .all()
    ])
    return all_teams, all_categories


# ---- PDF generator (single-column, linear, splittable tables)
def generate_pdf(report_type, data, columns, lineup_per_team=None, team_categories=None, race_date=None):
    """
    Produce un PDF in-memory.
    - team_composition & lineup: ogni team è un blocco verticale con tabella splittabile
    - altri report: tabella unica
    """
    buffer = io.BytesIO()
    # usa landscape per reports con molte colonne (riders)
    landscape_mode = report_type in ["riders", "riders_compact"]
    if landscape_mode:
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)
    else:
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18)

    styles = getSampleStyleSheet()
    elements = []

    # Titolo e filtri (semplice)
    elements.append(Paragraph(f"Report: {report_type.replace('_',' ').title()}", styles["Heading2"]))
    if race_date:
        elements.append(Paragraph(f"Race date: {race_date}", styles["Normal"]))
    elements.append(Spacer(1, 8))

    # Per team_composition / lineup: blocchi team uno sotto l'altro
    if report_type in ["team_composition", "lineup"] and lineup_per_team:
        # iterate teams in sorted order for stable output
        for team_name in sorted(lineup_per_team.keys()):
            riders = lineup_per_team[team_name]
            # Titolo team + capitano (team_categories stores team category; captain stored in rider dict in some variants)
            captain = ""
            # try to get captain from first rider if present, otherwise from team_categories/cannot assume
            if riders and isinstance(riders[0], dict):
                captain = riders[0].get("captain", "") or ""
            # Prefer explicit team_categories if used for captain_name fallback
            if not captain and team_categories:
                # team_categories stores category, not captain ; don't override
                pass

            title_txt = f"<b>{team_name}</b>"
            if captain:
                title_txt += f" — Capitano: {captain}"
            elements.append(Paragraph(title_txt, styles["Heading4"]))
            elements.append(Spacer(1, 4))

            # Table header depends on report_type: lineup includes race_date column
            header = ["Profile", "Cat.", "Name", "Status", "Signed Up", "Points"]
            if report_type == "lineup":
                header.append("Race Date")

            tbl_data = [header]
            for r in riders:
                # r can be dict with keys depending on how we built lineup_per_team
                profile = r.get("profile_id") if isinstance(r, dict) else getattr(r, "profile_id", "")
                category = r.get("category") if isinstance(r, dict) else getattr(r, "category", "")
                name = r.get("rider_name") if isinstance(r, dict) else (r.get("name") if isinstance(r, dict) else getattr(r, "name", ""))
                status = r.get("status") if isinstance(r, dict) else getattr(r, "member_status", "")
                signedup = r.get("signedup") if isinstance(r, dict) else getattr(r, "signedup", "")
                points = r.get("riderpoints") if isinstance(r, dict) else getattr(r, "riderpoints", "")
                row = [profile, category, name, status, signedup, points]
                if report_type == "lineup":
                    race_date_val = r.get("race_date") if isinstance(r, dict) else None
                    row.append(race_date_val or "")
                tbl_data.append(row)

            # Column widths tuned for A4; adjust if needed
            # If lineup, include extra width for Race Date
            if report_type == "lineup":
                colWidths = [55, 40, 140, 60, 50, 45, 60]
            else:
                colWidths = [60, 45, 170, 70, 55, 50]

            tbl = Table(tbl_data, colWidths=colWidths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#007bff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))

            elements.append(tbl)
            elements.append(Spacer(1, 14))  # spazio tra team

    else:
        # Tabella unica per riders/teams/etc.
        if not columns:
            columns = list(data[0].keys()) if data else []
        table_data = [columns] + [[row.get(col, "") for col in columns] for row in data]
        # autosize col widths (ReportLab will handle)
        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#007bff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(tbl)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---- Main route: export (HTML/CSV/XLSX/PDF)
@admin_bp.route("/reports/export")
@login_required
def export_report():
    report_type = request.args.get("report_type", "riders_compact").strip()
    category_filter = (request.args.get("category") or "").strip().upper()
    team_filter_raw = (request.args.get("team") or "").strip()
    fmt = (request.args.get("format") or request.args.get("fmt") or "html").lower()

    # Normalize 'tutti'
    if category_filter in ["", "TUTTI", "TUTTE", "ALL", "NONE"]:
        category_filter = None
    if team_filter_raw in ["", "TUTTI", "ALL", "NONE"]:
        team_filter_raw = None

    # Resolve team_filter_trc if user passed a TRC or a team name
    team_filter_trc = None
    if team_filter_raw:
        t_by_trc = Team.query.filter(Team.trc == team_filter_raw).first()
        if t_by_trc:
            team_filter_trc = t_by_trc.trc
        else:
            t_by_name = Team.query.filter(Team.name.ilike(f"%{team_filter_raw}%")).first()
            if t_by_name:
                team_filter_trc = t_by_name.trc

    data = []
    columns = []
    lineup_per_team = {}
    team_categories = {}
    race_date = None

    # ----------------------------
    # RIDERS / RIDERS_COMPACT
    # ----------------------------
    if report_type in ["riders", "riders_compact"]:
        q = db.session.query(
            WTRL_Rider.profile_id,
            WTRL_Rider.name,
            WTRL_Rider.category,
            WTRL_Rider.riderpoints,
            WTRL_Rider.member_status,
            Team.name.label("team_name"),
            Team.category.label("team_category")
        ).outerjoin(Team, Team.trc == WTRL_Rider.team_trc)

        if category_filter:
            q = q.filter(func.upper(Team.category) == category_filter)
        if team_filter_trc:
            q = q.filter(WTRL_Rider.team_trc == team_filter_trc)
        elif team_filter_raw:
            q = q.filter(Team.name.ilike(f"%{team_filter_raw}%"))

        rows = q.order_by(WTRL_Rider.name.asc()).all()

        aggregated = {}
        for r in rows:
            pid = r.profile_id
            team_name = r.team_name or "Senza Team"
            if pid not in aggregated:
                aggregated[pid] = {
                    "profile_id": pid,
                    "name": r.name,
                    "category": r.category,
                    "riderpoints": r.riderpoints,
                    "status": r.member_status,
                    "teams": []
                }
            aggregated[pid]["teams"].append(team_name)

        max_slots = max((len(set(v["teams"])) for v in aggregated.values()), default=0)
        for rider in aggregated.values():
            row = {
                "profile_id": rider["profile_id"],
                "name": rider["name"],
                "category": rider["category"]
            }
            unique_teams = sorted(set(rider["teams"]))
            for i, t in enumerate(unique_teams):
                row[f"Team {i+1}"] = t
            for i in range(len(unique_teams), max_slots):
                row[f"Team {i+1}"] = ""
            if report_type == "riders":
                row["riderpoints"] = rider["riderpoints"]
                row["status"] = rider["status"]
            data.append(row)

        base_cols = ["profile_id", "name", "category"]
        team_cols = [f"Team {i+1}" for i in range(max_slots)]
        columns = base_cols + (["riderpoints", "status"] if report_type == "riders" else []) + team_cols

    # ----------------------------
    # TEAM COMPOSITION
    # ----------------------------
    elif report_type == "team_composition":
        teams_q = Team.query.order_by(Team.name)
        if team_filter_raw:
            teams_q = teams_q.filter(Team.name.ilike(f"%{team_filter_raw}%"))
        if category_filter:
            teams_q = teams_q.filter(func.upper(Team.category) == category_filter)
        teams = teams_q.all()

        for t in teams:
            riders_q = WTRL_Rider.query.filter(WTRL_Rider.team_trc == t.trc).order_by(WTRL_Rider.name.asc())
            riders = riders_q.all()
            if not riders:
                continue

            team_categories[t.name] = t.category or "OTHER"
            lineup_per_team[t.name] = []
            for r in riders:
                rider_data = {
                    "profile_id": r.profile_id,
                    "category": t.category or "OTHER",
                    "status": r.member_status or "N/A",
                    "signedup": getattr(r, "signedup", ""),
                    "riderpoints": r.riderpoints,
                    "captain": t.captain_name or "",
                    "rider_name": r.name
                }
                lineup_per_team[t.name].append(rider_data)
                flat = rider_data.copy()
                flat["team_name"] = t.name
                data.append(flat)

        columns = ["team_name", "profile_id", "category", "status", "signedup", "riderpoints", "captain", "rider_name"]

    # ----------------------------
    # LINEUP
    # ----------------------------
    elif report_type == "lineup":
        race_date_obj = db.session.query(func.min(RaceLineup.race_date)).filter(RaceLineup.race_date >= func.current_date()).scalar()
        if not race_date_obj:
            if fmt == "html":
                all_teams, all_categories = get_filter_options()
                return render_template("admin/reports/index.html",
                                       report_type=report_type, rows=[], columns=[], teams=all_teams,
                                       categories=all_categories, lineup_per_team={}, team_categories={}, race_date="Nessuna gara futura")
            return "Nessuna gara futura", 400

        race_date = race_date_obj.strftime("%Y-%m-%d")
        q = db.session.query(
            RaceLineup.race_date,
            WTRL_Rider.profile_id,
            WTRL_Rider.name.label("rider_name"),
            WTRL_Rider.category,
            Team.name.label("team_name"),
            Team.category.label("team_category")
        ).join(WTRL_Rider, WTRL_Rider.profile_id == RaceLineup.profile_id)\
         .outerjoin(Team, Team.trc == WTRL_Rider.team_trc)\
         .filter(RaceLineup.race_date == race_date_obj)\
         .order_by(Team.name.asc(), WTRL_Rider.category.asc())

        if category_filter:
            q = q.filter(func.upper(Team.category) == category_filter)
        if team_filter_trc:
            q = q.filter(WTRL_Rider.team_trc == team_filter_trc)
        elif team_filter_raw:
            q = q.filter(Team.name.ilike(f"%{team_filter_raw}%"))

        rows = q.all()
        for r in rows:
            tname = r.team_name or "Senza Team"
            if tname not in lineup_per_team:
                lineup_per_team[tname] = []
                team_categories[tname] = r.team_category or "OTHER"
            lineup_per_team[tname].append({
                "profile_id": r.profile_id,
                "category": r.team_category or "OTHER",
                "rider_name": r.rider_name,
                "race_date": r.race_date.strftime("%Y-%m-%d")
            })
            data.append({
                "team": tname,
                "profile_id": r.profile_id,
                "rider_name": r.rider_name,
                "category": r.team_category or "OTHER",
                "race_date": r.race_date.strftime("%Y-%m-%d")
            })

        columns = ["team", "profile_id", "rider_name", "category", "race_date"]

    # ----------------------------
    # TEAMS
    # ----------------------------
    elif report_type == "teams":
        teams_data = db.session.query(
            Team.name, Team.trc, Team.category, Team.captain_name,
            func.count(WTRL_Rider.profile_id).label("n_riders")
        ).outerjoin(WTRL_Rider, WTRL_Rider.team_trc == Team.trc)\
         .group_by(Team.name, Team.trc, Team.category, Team.captain_name)\
         .order_by(Team.name.asc()).all()

        for t in teams_data:
            data.append({
                "name": t.name,
                "trc": t.trc,
                "category": t.category,
                "captain": t.captain_name,
                "n_riders": t.n_riders
            })
        columns = ["name", "trc", "category", "captain", "n_riders"]

    # ----------------------------
    # ROUND STANDINGS (Classifica Punti Team)
    # ----------------------------
    elif report_type == "round_standings":
        q = db.session.query(
            Team.name,
            Team.category,
            Team.captain_name,
            func.coalesce(func.sum(WTRL_Rider.riderpoints), 0).label("total_points"),
            func.count(WTRL_Rider.profile_id).label("n_riders")
        ).outerjoin(WTRL_Rider, WTRL_Rider.team_trc == Team.trc)

        if category_filter:
            q = q.filter(func.upper(Team.category) == category_filter)
        if team_filter_raw:
            q = q.filter(Team.name.ilike(f"%{team_filter_raw}%"))

        q = q.group_by(Team.name, Team.category, Team.captain_name)\
             .order_by(func.coalesce(func.sum(WTRL_Rider.riderpoints), 0).desc())

        standings = q.all()
        for t in standings:
            data.append({
                "team": t.name,
                "category": t.category or "OTHER",
                "captain": t.captain_name or "",
                "n_riders": t.n_riders,
                "total_points": t.total_points
            })
        columns = ["team", "category", "captain", "n_riders", "total_points"]

    # ----------------------------
    # OUTPUT
    # ----------------------------
    if fmt == "csv":
        import pandas as pd
        import pandas as pd
        df = pd.DataFrame(data, columns=columns)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(buf, download_name=f"{report_type}.csv", as_attachment=True)

    if fmt in ["xlsx", "excel"]:
        import pandas as pd
        import pandas as pd
        df = pd.DataFrame(data, columns=columns)
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return send_file(buf, download_name=f"{report_type}.xlsx", as_attachment=True)

    if fmt == "pdf":
        pdf_buf = generate_pdf(report_type, data, columns, lineup_per_team=lineup_per_team, team_categories=team_categories, race_date=race_date)
        return send_file(pdf_buf, download_name=f"{report_type}.pdf", as_attachment=True)

    all_teams, all_categories = get_filter_options()
    return render_template(
        "admin/reports/index.html",
        report_type=report_type,
        rows=data,
        columns=columns,
        category_filter=category_filter,
        team_filter=team_filter_raw,
        teams=all_teams,
        categories=all_categories,
        lineup_per_team=lineup_per_team,
        team_categories=team_categories,
        race_date=race_date
    )
