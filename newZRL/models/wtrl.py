from newZRL import db




# ==============================
# Competitions / Leagues / Divisions / Races
# ==============================
class WTRLCompetition(db.Model):
    __tablename__ = "wtrl_competitions"
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"))
    leagues = db.relationship("WTRLLeague", backref="competition", lazy=True)


class WTRLLeague(db.Model):
    __tablename__ = "wtrl_leagues"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    competition_id = db.Column(db.String(10), db.ForeignKey("wtrl_competitions.id"))
    divisions = db.relationship("WTRLDivision", backref="league", lazy=True)


class WTRLDivision(db.Model):
    __tablename__ = "wtrl_divisions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(10), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey("wtrl_leagues.id"))
    races = db.relationship("WTRLRace", backref="division", lazy=True)


class WTRLRace(db.Model):
    __tablename__ = "wtrl_races"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    race_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255))
    format = db.Column(db.String(20))
    division_id = db.Column(db.Integer, db.ForeignKey("wtrl_divisions.id"))
