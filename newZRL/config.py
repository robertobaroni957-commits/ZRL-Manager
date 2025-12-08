import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Usa la variabile d'ambiente DATABASE_URL o fallback all'URL esterno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql+psycopg2://zrlmanager_db_user:teF9dx9z82SvMVHq6wT6MZPQ1c6nZmyQ@dpg-d4res6ngi27c73amg2e0-a.frankfurt-postgres.render.com/zrlmanager_db'
)

db = SQLAlchemy(app)

@app.route("/")
def home():
    return "Hello, ZRL Manager is running!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
