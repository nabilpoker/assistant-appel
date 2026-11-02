"""Point d'entrée : démarre le serveur local et ouvre l'application dans sa propre fenêtre."""
import threading
import time
import webbrowser

from server import app

PORT = 8000
URL = f"http://127.0.0.1:{PORT}/"


def run_server():
    # 127.0.0.1 : accessible uniquement depuis ce PC
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(1)
    try:
        import webview
        # Fenêtre indépendante, redimensionnable, toujours au-dessus des autres applications
        webview.create_window(
            "Damia", URL,
            width=440, height=820, min_size=(380, 560), on_top=True,
        )
        webview.start()
    except Exception:
        # Repli : ouverture dans le navigateur si la fenêtre intégrée ne démarre pas
        webbrowser.open(URL)
        while True:
            time.sleep(3600)
