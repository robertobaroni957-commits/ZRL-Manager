# Nome del Progetto

Breve descrizione: progetto Flask + SQLAlchemy per la gestione della ZRL del TEAM INOX 

## Requisiti

- Python 3.10+
- MYSQL (o altro DB supportato)
- pip

## Variabili d'ambiente

Copia .env.example in .env e modifica i valori locali:
- FLASK_APP=run.py
- FLASK_ENV=development
- SECRET_KEY=...
- DATABASE_URL=postgresql://user:pass@host:port/dbname

## Installazione locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade   # se usi Flask-Migrate
flask run
```

## Test

```bash
pytest
```

## Licenza

Scegli una licenza (es. MIT).