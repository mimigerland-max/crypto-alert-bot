"""
Bot "sniper" spécifique à pump.fun. Se connecte en direct (WebSocket)
au flux public et gratuit de PumpPortal.fun, qui pousse un événement
la seconde même où un nouveau token est créé sur pump.fun.

Contrairement au reste du bot (qui vérifie toutes les 5 minutes), ce
script reste connecté en continu pendant la durée du job GitHub
Actions (~5h50 max), pour ne rater aucun lancement pendant ce temps.
Le workflow le relance automatiquement ensuite (voir pump_sniper.yml).
"""

import json
import os
import threading
import time
import websocket

from discord_alert import send_sniper_alert

PUMPPORTAL_WS_URL = "wss://pumpportal.fun/api/data"
MAX_RUNTIME_SECONDS = int(5.83 * 3600)  # ~5h50, reste sous la limite GitHub Actions de 6h

# Filtre anti-spam : ignore les lancements avec moins de X SOL d'achat
# initial (pump.fun crée des centaines de tokens/heure, sans filtre ton
# Discord serait noyé). Modifiable via variable d'environnement.
MIN_SOL_TO_ALERT = float(os.environ.get("MIN_SOL_TO_ALERT", "2"))


def on_open(ws):
    print("[pump_sniper] Connecté à PumpPortal, abonnement aux nouveaux tokens...")
    ws.send(json.dumps({"method": "subscribeNewToken"}))


def on_message(ws, message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return

    if data.get("txType") != "create":
        return  # on ignore les événements qui ne sont pas des créations

    sol_amount = data.get("solAmount", 0)
    if sol_amount < MIN_SOL_TO_ALERT:
        return  # filtre anti-spam

    name = data.get("name", "?")
    symbol = data.get("symbol", "?")
    mint = data.get("mint", "")
    pump_url = f"https://pump.fun/{mint}" if mint else "(lien indisponible)"

    print(f"[pump_sniper] Nouveau : {name} ({symbol}) - {sol_amount} SOL - {pump_url}")
    send_sniper_alert(f"{name} ({symbol})", "solana (pump.fun)", pump_url)


def on_error(ws, error):
    print(f"[pump_sniper] Erreur WebSocket : {error}")


def on_close(ws, close_status_code, close_msg):
    print("[pump_sniper] Connexion fermée.")


def stop_after_timeout(ws):
    time.sleep(MAX_RUNTIME_SECONDS)
    print("[pump_sniper] Durée max atteinte, fermeture propre avant la limite GitHub Actions.")
    ws.close()


def run():
    ws = websocket.WebSocketApp(
        PUMPPORTAL_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    timer_thread = threading.Thread(target=stop_after_timeout, args=(ws,), daemon=True)
    timer_thread.start()

    ws.run_forever(ping_interval=30, ping_timeout=10)


if __name__ == "__main__":
    run()
