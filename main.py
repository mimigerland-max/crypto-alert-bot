"""
Point d'entrée du bot. Version sans Reddit ni X (fermés/payants).
Utilise CoinGecko (coins tendance) + DexScreener (nouveaux tokens
boostés), tous les deux gratuits et sans clé API.
"""

from coingecko_trending import get_trending_coins
from dexscreener_new_tokens import get_boosted_tokens
from history import load_history, save_scan_result
from discord_alert import send_alert

TOP_N_TO_WATCH = 10
MAX_BOOSTED_TO_CHECK = 15


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
            send_alert(
                f"{coin['symbol']} (CoinGecko trending)",
                current_mentions=coin["rank"],
                average=TOP_N_TO_WATCH,
                ratio=TOP_N_TO_WATCH / coin["rank"],
            )
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
        current_state[key] = 1  # présence = 1, pas de classement ici

        if key not in history:
            print(f"[analyse] Nouveau token boosté : {token['id']} ({token['chain']})")
            send_alert(
                f"{token['id']} ({token['chain']}, DexScreener)",
                current_mentions=1,
                average=1,
                ratio=1,
            )
            alerts += 1

    return alerts


def run():
    print("=== Scan en cours (CoinGecko + DexScreener) ===")

    history = load_history()
    current_state = {}

    alerts_sent = 0
    alerts_sent += check_coingecko(history, current_state)
    alerts_sent += check_dexscreener(history, current_state)

    save_scan_result(history, current_state)

    print(f"=== Scan terminé. {alerts_sent} alerte(s) envoyée(s). ===")


if __name__ == "__main__":
    run()
