# newZRL/models/season.py
from newZRL import db

class Season(db.Model):
    __tablename__ = "seasons"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Relazione con Round
    rounds = db.relationship("Round", back_populates="season", cascade="all, delete-orphan")
