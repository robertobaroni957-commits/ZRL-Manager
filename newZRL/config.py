import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersegreto")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://RB:Ro12ba-12@localhost/zrl"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
