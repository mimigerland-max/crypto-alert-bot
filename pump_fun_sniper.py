"""
Bot sniper pump.fun via WebSocket PumpPortal.
Reste connecté en continu (~5h50) pour capter les créations en temps réel.
"""

import json
import os
import threading
import time
import websocket

from config import (
    HISTORY_FILE,
    MIN_HIGH_CONVICTION_SCORE,
    MIN_SOL_TO_ALERT as DEFAULT_MIN_SOL,
    PUMP_SCORE_DELAY_SECONDS,
)
from dexscreener_enrich import enrich_token
from discord_alert import send_pump_alert
from history import load_history, save_scan_result, was_seen
from memecoin_score import score_memecoin

PUMPPORTAL_WS_URL = "wss://pumpportal.fun/api/data"
MAX_RUNTIME_SECONDS = int(5.83 * 3600)
MIN_SOL_TO_ALERT = float(os.environ.get("MIN_SOL_TO_ALERT", str(DEFAULT_MIN_SOL)))

_seen_this_session = set()


def _pump_key(mint):
    return f"pump:{mint}"


def on_open(ws):
    print("[pump_sniper] Connecté, abonnement aux nouveaux tokens...")
    ws.send(json.dumps({"method": "subscribeNewToken"}))


def _evaluate_and_maybe_alert(mint, name, symbol, sol_amount, pump_url, key):
    """
    Appelé après PUMP_SCORE_DELAY_SECONDS, une fois que le marché a eu le
    temps de se former un minimum. Enrichit via DexScreener puis score le
    token. N'alerte QUE si le score dépasse MIN_HIGH_CONVICTION_SCORE.

    Rappel : un score élevé signale un setup statistiquement plus favorable
    (liquidité saine, forte pression acheteuse, momentum positif, activité
    réelle). Ce n'est PAS une garantie de x2/x3 — aucun filtre ne peut
    garantir un pump, le marché reste imprévisible et manipulable.
    """
    enriched = enrich_token(mint, "solana")
    score, reasons, passed = score_memecoin(enriched, initial_sol=sol_amount, is_boosted=False)

    if not passed or score < MIN_HIGH_CONVICTION_SCORE:
        print(
            f"[pump_sniper] {name} ({symbol}) écarté : score {score}/100 "
            f"(seuil forte conviction = {MIN_HIGH_CONVICTION_SCORE})."
        )
        return

    print(f"[pump_sniper] FORTE CONVICTION : {name} ({symbol}) - score {score}/100")
    send_pump_alert(
        name, symbol, mint, sol_amount, pump_url,
        score=score, reasons=reasons, enriched=enriched,
    )

    history = load_history()
    save_scan_result(history, {key: 1})


def on_message(ws, message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return

    if data.get("txType") != "create":
        return

    sol_amount = float(data.get("solAmount") or 0)
    if sol_amount < MIN_SOL_TO_ALERT:
        return

    name = data.get("name", "?")
    symbol = data.get("symbol", "?")
    mint = data.get("mint", "")
    if not mint:
        return

    key = _pump_key(mint)
    if mint in _seen_this_session:
        return
    _seen_this_session.add(mint)

    history = load_history()
    if was_seen(history, key):
        return

    pump_url = f"https://pump.fun/{mint}"
    print(
        f"[pump_sniper] Détecté : {name} ({symbol}) - {sol_amount:.2f} SOL "
        f"— évaluation dans {PUMP_SCORE_DELAY_SECONDS}s pour filtrer les faux signaux..."
    )

    timer = threading.Timer(
        PUMP_SCORE_DELAY_SECONDS,
        _evaluate_and_maybe_alert,
        args=(mint, name, symbol, sol_amount, pump_url, key),
    )
    timer.daemon = True
    timer.start()


def on_error(ws, error):
    print(f"[pump_sniper] Erreur WebSocket : {error}")


def on_close(ws, close_status_code, close_msg):
    print("[pump_sniper] Connexion fermée.")


def stop_after_timeout(ws):
    time.sleep(MAX_RUNTIME_SECONDS)
    print("[pump_sniper] Durée max atteinte, fermeture.")
    ws.close()


def run():
    print(f"[pump_sniper] Seuil min : {MIN_SOL_TO_ALERT} SOL | historique : {HISTORY_FILE}")
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
