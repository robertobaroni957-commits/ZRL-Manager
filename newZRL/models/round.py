from newZRL import db

class Round(db.Model):
    __tablename__ = "rounds"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    season_id = db.Column(db.Integer, db.ForeignKey("seasons.id"), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)  
    name = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    logo_url = db.Column(db.String(255))  # opzionale

    is_active = db.Column(db.Boolean, default=True)

    # Relazioni
    season = db.relationship("Season", back_populates="rounds")
    races = db.relationship("Race", back_populates="round", cascade="all, delete-orphan")
