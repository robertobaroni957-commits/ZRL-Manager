from newZRL import db
from sqlalchemy import BigInteger, UniqueConstraint

class RaceLineup(db.Model):
    __tablename__ = "race_lineup"

    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.String(50), nullable=False)
    race_date = db.Column(db.Date, nullable=False)
    # team_trc = db.Column(db.String(10), nullable=False) # Removed
    wtrl_rider_id = db.Column(db.String(100), db.ForeignKey("wtrl_riders.id"), nullable=False)

    # Relazione con WTRL_Rider
    rider = db.relationship("WTRL_Rider", backref=db.backref("lineups", lazy="dynamic"))
    
    # Vincolo per prevenire duplicati (opzionale, ma consigliato per integrità)
    __table_args__ = (
        UniqueConstraint('race_id', 'wtrl_rider_id', name='_race_wtrl_rider_uc'),
    )