from newZRL import db

class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)  # ✅ Ripristinato

    def __repr__(self):
        return f"<League {self.name}>"
