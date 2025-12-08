from newZRL import db
from newZRL.models.team import Team
from newZRL.models.rider import Rider

class RaceLineup(db.Model):
    __tablename__ = "race_lineup"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    race_date = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    profile_id = db.Column(db.BigInteger, db.ForeignKey("riders.profile_id"))

    team = db.relationship(Team, backref=db.backref("lineups", lazy=True))
    rider = db.relationship(Rider, backref=db.backref("lineups", lazy=True))

    def __repr__(self):
        return f"<RaceLineup {self.race_date} team={self.team.name} rider={self.rider.name}>"
