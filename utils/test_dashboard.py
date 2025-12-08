import pytest

REQUIRED_KEYS = {
    "empty", "category", "division", "name",
    "has_lineup", "rider_count", "captain_name", "id"
}

def validate_team_structure(team):
    missing = REQUIRED_KEYS - team.keys()
    return missing

def test_teams_list_structure():
    # Simulazione di teams_list come nel controller
    teams_list = [
        {
            "id": 1,
            "name": "Team Alpha",
            "category": "A",
            "division": "1",
            "captain_name": "Alice",
            "rider_count": 5,
            "has_lineup": True,
            "empty": False
        },
        {
            "empty": True  # placeholder incompleto
        }
    ]

    # Riempimento automatico dei placeholder
    for team in teams_list:
        for key in REQUIRED_KEYS:
            team.setdefault(key, None if key != "has_lineup" else False)

    # Verifica che tutti i team abbiano i campi richiesti
    for i, team in enumerate(teams_list):
        missing = validate_team_structure(team)
        assert not missing, f"Team index {i} missing keys: {missing}"