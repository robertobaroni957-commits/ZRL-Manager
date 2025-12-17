from flask import Blueprint, jsonify
from newZRL.models.team import Team # <-- ASSUMENDO SIA QUI!

# Devi importare anche l'istanza di db per la query, 
# se non usi db.session.query()
from newZRL import db 

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/rosters', methods=['GET'])
def get_all_rosters():
    """
    Recupera tutti i roster delle squadre ZRL e li formatta in JSON.
    ---
    responses:
      200:
        description: Un elenco di roster delle squadre ZRL.
        schema:
          type: object
          properties:
            team_id_key:
              type: object
              properties:
                name:
                  type: string
                  description: Il nome della squadra.
                captain:
                  type: string
                  description: Il nome del capitano della squadra.
                riders:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        description: Il nome del ciclista.
                      avatar:
                        type: string
                        description: URL dell'avatar del ciclista.
    tags:
      - Rosters
    """
    rosters = {}
    
    try:
        # Recupera tutti i team (potresti filtrare per stagione, competition_class, ecc.)
        teams_data = db.session.execute(db.select(Team)).scalars().all() 
        
        for team in teams_data:
            riders_list = []
            
            # Utilizza la relazione wtrl_riders fornita dal tuo modello
            for rider in team.wtrl_riders: 
                riders_list.append({
                    # Ipotizziamo che la classe WTRL_Rider abbia i campi 'name' e 'avatar_url'
                    'name': rider.name,     
                    'avatar': rider.avatar # Changed from avatar_url to avatar
                })
            
            # L'ID univoco del team che il frontend usa per il click: Categoria + Divisione
            # Esempio: "A" + "1" = "A1"
            team_id_key = f"{team.category}{team.division}" 
            
            rosters[team_id_key] = {
                'name': team.name,
                'captain': team.captain_name, # Usa il campo captain_name dal tuo modello
                'riders': riders_list
            }
            
    except Exception as e:
        return jsonify({"error": f"Errore nel recupero dati o nella modellazione: {str(e)}"}), 500

    return jsonify(rosters)