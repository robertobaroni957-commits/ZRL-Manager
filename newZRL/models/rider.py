from newZRL import db
from sqlalchemy.orm import foreign

class Rider(db.Model):
    __tablename__ = "riders"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.BigInteger, unique=True, nullable=False)
    avatar = db.Column(db.String(255))
    category = db.Column(db.String(10))
    member_status = db.Column(db.String(50))

    # Relazione verso WTRL_Rider (uno-a-uno)
    wtrl_data = db.relationship(
        "newZRL.models.wtrl_rider.WTRL_Rider",
        primaryjoin="Rider.profile_id==foreign(WTRL_Rider.profile_id)",
        uselist=False,
        viewonly=True
    )