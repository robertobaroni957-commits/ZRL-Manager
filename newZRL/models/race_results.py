from datetime import datetime
from newZRL import db

class RaceResultsTeam(db.Model):
    __tablename__ = "race_results_teams"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    class_id = db.Column(db.String(50), nullable=False)
    race = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.trc"), nullable=False)
    finp = db.Column(db.Integer, default=0)
    pbp = db.Column(db.Integer, default=0)
    totp = db.Column(db.Integer, default=0)
    falp = db.Column(db.Integer, default=0)
    ftsp = db.Column(db.Integer, default=0)
    time_result = db.Column(db.String(50))
    distance_result = db.Column(db.String(50))
    rank = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    riders = db.relationship("RaceResultsRider", backref="team_result", cascade="all, delete-orphan")


class RaceResultsRider(db.Model):
    __tablename__ = "race_results_riders"

    id = db.Column(db.Integer, primary_key=True)
    race_team_result_id = db.Column(db.Integer, db.ForeignKey("race_results_teams.id"), nullable=False)
    rider_id = db.Column(db.String(100), db.ForeignKey("wtrl_riders.id"), nullable=False)
    finp = db.Column(db.Integer, default=0)
    pbp = db.Column(db.Integer, default=0)
    totp = db.Column(db.Integer, default=0)
    falp = db.Column(db.Integer, default=0)
    ftsp = db.Column(db.Integer, default=0)
    time_result = db.Column(db.String(50))
    distance_result = db.Column(db.String(50))
    wkg = db.Column(db.Float)
    watts = db.Column(db.Float)
    gap = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RoundStanding(db.Model):
    __tablename__ = "round_standings"

    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    class_id = db.Column(db.String(50), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.trc"), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

