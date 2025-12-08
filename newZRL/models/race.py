from newZRL import db

class Race(db.Model):
    __tablename__ = "races"

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"))
    name = db.Column(db.String(255))
    race_date = db.Column(db.Date)
    format = db.Column(db.String(50))
    world = db.Column(db.String(50))
    course = db.Column(db.String(255))
    laps = db.Column(db.Integer)
    distance_km = db.Column(db.Float)
    elevation_m = db.Column(db.Float)
    powerups = db.Column(db.Text)
    fal_segments = db.Column(db.Text)
    fts_segments = db.Column(db.Text)
    rules = db.Column(db.Text)
    segments = db.Column(db.Text)
    duration = db.Column(db.Integer)
    difficulty = db.Column(db.Integer)
    leadin_distance = db.Column(db.Float)
    leadin_ascent = db.Column(db.Float)
    category = db.Column(db.String(5))

    active = db.Column(db.Integer, default=1)           # aggiunto
    external_id = db.Column(db.String(50))              # aggiunto

    round = db.relationship("Round", back_populates="races")
