# run.py
import os
import sys

from newZRL import create_app

app = create_app()

def main():
    # Controlla se siamo in locale (es. non in Render)
    is_local = "RENDER" not in os.environ

    if is_local:
        # Apri il browser automaticamente in locale
        import webbrowser
        webbrowser.open("http://127.0.0.1:5000/")

        # Porta di default per sviluppo
        port = 5000
        debug = True
    else:
        # Render imposta la porta tramite env variable
        port = int(os.environ.get("PORT", 10000))
        debug = False  # non usare debug in produzione

    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=is_local)

if __name__ == "__main__":
    main()
