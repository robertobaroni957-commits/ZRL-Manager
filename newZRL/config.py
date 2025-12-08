import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://zrlmanager_db_user:teF9dx9z82SvMVHq6wT6MZPQ1c6nZmyQ@dpg-d4res6ngi27c73amg2e0-a.frankfurt-postgres.render.com/zrlmanager_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")

db = SQLAlchemy(app)

@app.route("/")
def home():
    return "Hello, ZRL Manager is running!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
