"""
Point d'entrée du bot. Version sans Reddit ni X (fermés/payants).
Utilise CoinGecko (coins tendance) + DexScreener (nouveaux tokens
boostés), tous les deux gratuits et sans clé API.
"""

from coingecko_trending import get_trending_coins
from dexscreener_new_tokens import get_boosted_tokens
from dexscreener_latest_profiles import get_latest_new_tokens
from history import load_history, save_scan_result
from discord_alert import send_trending_alert, send_new_token_alert, send_sniper_alert

TOP_N_TO_WATCH = 10
MAX_BOOSTED_TO_CHECK = 15
MAX_NEW_TOKENS_TO_CHECK = 15


def check_coingecko(history, current_state):
    """Alerte si un coin entre pour la 1ère fois dans le top CoinGecko."""
    trending = get_trending_coins()
    if not trending:
        print("[coingecko] Aucune donnée récupérée.")
        return 0

    print("[coingecko] Coins tendance en ce moment :")
    for coin in trending:
        print(f"    #{coin['rank']} {coin['name']} ({coin['symbol']})")

    alerts = 0
    for coin in trending[:TOP_N_TO_WATCH]:
        key = f"cg:{coin['symbol']}"
        current_state[key] = coin["rank"]

        if key not in history:
            print(f"[analyse] {coin['symbol']} : NOUVEAU dans le top CoinGecko (rang #{coin['rank']})")
            send_trending_alert(coin["symbol"], coin["rank"], TOP_N_TO_WATCH)
            alerts += 1

    return alerts


def check_dexscreener(history, current_state):
    """Alerte si un token boosté apparaît pour la 1ère fois."""
    boosted = get_boosted_tokens()
    if not boosted:
        print("[dexscreener] Aucune donnée récupérée.")
        return 0

    print(f"[dexscreener] {len(boosted)} tokens boostés récupérés.")

    alerts = 0
    for token in boosted[:MAX_BOOSTED_TO_CHECK]:
        key = f"dex:{token['id']}"
        current_state[key] = 1

        if key not in history:
            print(f"[analyse] Nouveau token boosté : {token['id']} ({token['chain']})")
            send_new_token_alert(token["id"], token["chain"], token["description"])
            alerts += 1

    return alerts


def check_sniper(history, current_state):
    """Alerte sur les tokens FLAMBANT NEUFS (avant même d'être boostés)."""
    new_tokens = get_latest_new_tokens()
    if not new_tokens:
        print("[sniper] Aucune donnée récupérée.")
        return 0

    print(f"[sniper] {len(new_tokens)} tokens tout neufs récupérés.")

    alerts = 0
    for token in new_tokens[:MAX_NEW_TOKENS_TO_CHECK]:
        key = f"sniper:{token['id']}"
        current_state[key] = 1

        if key not in history:
            print(f"[analyse] [SNIPER] Nouveau token : {token['id']} ({token['chain']})")
            send_sniper_alert(token["id"], token["chain"], token["description"])
            alerts += 1

    return alerts


def run():
    print("=== Scan en cours (CoinGecko + DexScreener + Sniper) ===")

    history = load_history()
    current_state = {}

    alerts_sent = 0
    alerts_sent += check_coingecko(history, current_state)
    alerts_sent += check_dexscreener(history, current_state)
    alerts_sent += check_sniper(history, current_state)

    save_scan_result(history, current_state)

    print(f"=== Scan terminé. {alerts_sent} alerte(s) envoyée(s). ===")


if __name__ == "__main__":
    run()
