# run.py
import webbrowser
from newZRL import create_app

app = create_app()

if __name__ == "__main__":
    # Apri il browser automaticamente solo una volta
    webbrowser.open("http://127.0.0.1:5000/")
    # Disabilita l'autoreloader per evitare doppie istanze
    app.run(debug=True, use_reloader=False)
