from datetime import datetime
from newZRL import db

class Team(db.Model):
    __tablename__ = "teams"

    trc = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    category = db.Column(db.String(10))
    division = db.Column(db.String(50))
    wtrl_team_id = db.Column(db.Integer)
    jersey_name = db.Column(db.String(255))
    jersey_image = db.Column(db.String(255))
    recruiting = db.Column(db.Boolean, default=False)
    is_dev = db.Column(db.Boolean, default=False)
    competition_class = db.Column(db.String(50))
    competition_season = db.Column(db.String(10))
    competition_year = db.Column(db.Integer)
    competition_round = db.Column(db.Integer)
    competition_status = db.Column(db.String(50))
    member_count = db.Column(db.Integer)
    members_remaining = db.Column(db.Integer)
    captain_name = db.Column(db.String(255))
    captain_profile_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazione con WTRL_Rider
    wtrl_riders = db.relationship("WTRL_Rider", back_populates="team")
