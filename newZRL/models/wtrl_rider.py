from datetime import datetime
from newZRL import db

class WTRL_Rider(db.Model):
    __tablename__ = "wtrl_riders"

    id = db.Column(db.String(100), primary_key=True)
    team_trc = db.Column(db.Integer, db.ForeignKey("teams.trc"), nullable=False)
    profile_id = db.Column(db.BigInteger, nullable=False, index=True) # Removed unique=True
    tmuid = db.Column(db.Integer)
    name = db.Column(db.String(255))
    avatar = db.Column(db.String(255))
    member_status = db.Column(db.String(50))
    signedup = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(5))
    zftp = db.Column(db.Float)
    zftpw = db.Column(db.Float)
    zmap = db.Column(db.Float)
    zmapw = db.Column(db.Float)
    riderpoints = db.Column(db.Integer)
    teams = db.Column(db.Integer)
    appearances_round = db.Column(db.Integer)
    appearances_season = db.Column(db.Integer)
    user_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazione con Team
    team = db.relationship("Team", back_populates="wtrl_riders")
