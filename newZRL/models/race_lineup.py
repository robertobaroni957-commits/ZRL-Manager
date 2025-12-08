from newZRL import db
from sqlalchemy import BigInteger, UniqueConstraint

class RaceLineup(db.Model):
    __tablename__ = "race_lineup"

    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.String(50), nullable=False)
    race_date = db.Column(db.Date, nullable=False)
    team_trc = db.Column(db.String(10), nullable=False)

    # 🛑 FIX: La colonna DB è 'rider_id', ma il tuo controller vuole 'profile_id'.
    # Usiamo il nome dell'attributo Python 'profile_id' che mappa alla colonna DB 'rider_id'.
    # E correggiamo il target della ForeignKey a 'wtrl_riders.profile_id'.
    profile_id = db.Column("rider_id", BigInteger, 
                           db.ForeignKey("wtrl_riders.profile_id"), 
                           nullable=False)

    # Relazione con WTRL_Rider (usa profile_id corretto)
    rider = db.relationship("WTRL_Rider", 
                            backref=db.backref("lineups", lazy="dynamic"),
                            primaryjoin="RaceLineup.profile_id == WTRL_Rider.profile_id",
                            viewonly=True)
    
    # Vincolo per prevenire duplicati (opzionale, ma consigliato per integrità)
    __table_args__ = (
        UniqueConstraint('race_id', 'rider_id', name='_race_rider_uc'),
    )