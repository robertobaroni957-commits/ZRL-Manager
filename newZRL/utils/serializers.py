from datetime import date, datetime

def serialize_model(obj):
    """
    Converte un oggetto SQLAlchemy in un dizionario serializzabile in JSON.
    Gestisce automaticamente i campi datetime e date.
    """
    if obj is None:
        return None

    serialized = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, (date, datetime)):
            value = value.isoformat()
        serialized[column.name] = value
    return serialized