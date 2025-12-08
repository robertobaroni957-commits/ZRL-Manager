# newZRL/utils/race_utils.py

from datetime import date
from newZRL import db
from newZRL.models.race import Race
from newZRL.models.race_lineup import RaceLineup

# ================================
# Restituisce la prossima gara disponibile (>= oggi)
# ================================
def get_next_race_date(team_id=None):
    today = date.today()
    race = db.session.query(Race)\
        .filter(Race.race_date >= today)\
        .order_by(Race.race_date.asc())\
        .first()
    return race.race_date if race else None

# ================================
# Controlla se un team ha già selezionato una formazione in una data specifica
# ================================
def validate_race_selection(team_id, race_date):
    delegate = db.session.query(RaceLineup)\
        .filter_by(team_id=team_id, race_date=race_date)\
        .first()
    return delegate is not None

# ================================
# Salva la formazione dei rider per una gara
# ================================
def save_race_selection(team_id, race_date, rider_ids):
    # elimina eventuali lineup esistenti
    db.session.query(RaceLineup)\
        .filter_by(team_id=team_id, race_date=race_date)\
        .delete()
    # aggiungi nuovi rider
    for profile_id in rider_ids:
        rl = RaceLineup(team_id=team_id, race_date=race_date, profile_id=profile_id)
        db.session.add(rl)
    db.session.commit()
