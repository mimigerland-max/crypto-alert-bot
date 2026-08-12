"""
Point d'entrée du bot de scan périodique.
Sources : Reddit (optionnel) + CoinGecko + DexScreener boostés + profils neufs.
"""

import os

from coingecko_trending import get_trending_coins
from config import (
    COINGECKO_RANK_JUMP_THRESHOLD,
    MAX_BOOSTED_TO_CHECK,
    MAX_NEW_TOKENS_TO_CHECK,
    MIN_BREAKOUT_SCORE,
    MIN_LIQUIDITY_USD,
    MIN_MENTIONS_TO_ALERT,
    SPIKE_THRESHOLD_MULTIPLIER,
    TOP_N_TO_WATCH,
)
from dexscreener_enrich import enrich_token
from dexscreener_latest_profiles import get_latest_new_tokens
from dexscreener_new_tokens import get_boosted_tokens
from discord_alert import (
    send_alert,
    send_new_token_alert,
    send_sniper_alert,
    send_trending_alert,
)
from history import average_mentions, last_value, load_history, save_scan_result, was_seen
from memecoin_score import score_memecoin


def check_reddit(history, current_state):
    """Scan Reddit si les identifiants sont configurés."""
    if not os.environ.get("REDDIT_CLIENT_ID") or not os.environ.get("REDDIT_CLIENT_SECRET"):
        print("[reddit] Identifiants absents, scan ignoré.")
        return 0

    from reddit_scanner import count_mentions

    try:
        counts = count_mentions()
    except RuntimeError as e:
        print(f"[reddit] {e}")
        return 0

    alerts = 0
    for coin, current in counts.items():
        key = f"reddit:{coin}"
        current_state[key] = current

        average = average_mentions(history, key)
        if average == 0:
            continue

        ratio = current / average
        if current >= MIN_MENTIONS_TO_ALERT and ratio >= SPIKE_THRESHOLD_MULTIPLIER:
            if current != last_value(history, key):
                print(f"[reddit] Pic {coin} : {current} mentions (x{ratio:.1f})")
                send_alert(coin, current, average, ratio)
                alerts += 1

    return alerts


def check_coingecko(history, current_state):
    """Alerte si nouveau dans le top ou grosse montée de rang."""
    trending = get_trending_coins()
    if not trending:
        print("[coingecko] Aucune donnée récupérée.")
        return 0

    print("[coingecko] Coins tendance :")
    for coin in trending:
        print(f"    #{coin['rank']} {coin['name']} ({coin['symbol']})")

    alerts = 0
    for coin in trending[:TOP_N_TO_WATCH]:
        key = f"cg:{coin['symbol']}"
        rank = coin["rank"]
        current_state[key] = rank

        previous_rank = last_value(history, key)
        first_time = not was_seen(history, key)
        rank_jump = (
            previous_rank is not None
            and rank < previous_rank
            and (previous_rank - rank) >= COINGECKO_RANK_JUMP_THRESHOLD
        )

        if first_time:
            print(f"[coingecko] NOUVEAU top : {coin['symbol']} (#{rank})")
            send_trending_alert(coin["symbol"], rank, TOP_N_TO_WATCH)
            alerts += 1
        elif rank_jump:
            print(f"[coingecko] MONTÉE : {coin['symbol']} #{previous_rank} -> #{rank}")
            send_trending_alert(coin["symbol"], rank, TOP_N_TO_WATCH, previous_rank=previous_rank)
            alerts += 1

    return alerts


def _process_dex_token(token, history, current_state, prefix, alert_fn, label):
    """Filtre par liquidité, enrichit et envoie l'alerte si nouveau."""
    key = f"{prefix}:{token['id']}"

    if was_seen(history, key):
        current_state[key] = 1
        return 0

    enriched = enrich_token(token["token_address"], token["chain"])
    if enriched and enriched["liquidity_usd"] < MIN_LIQUIDITY_USD:
        print(
            f"[{label}] {token['id']} ignoré : liquidité "
            f"${enriched['liquidity_usd']:,.0f} < ${MIN_LIQUIDITY_USD:,.0f}"
        )
        return 0

    current_state[key] = 1
    print(f"[{label}] Alerte : {token['id']}")
    alert_fn(
        token_id=token["id"],
        chain=token["chain"],
        description=token["description"],
        symbol=enriched["symbol"] if enriched else None,
        url=(enriched or token)["url"],
        enriched=enriched,
    )
    return 1


def check_dexscreener(history, current_state):
    boosted = get_boosted_tokens()
    if not boosted:
        print("[dexscreener] Aucune donnée récupérée.")
        return 0

    print(f"[dexscreener] {len(boosted)} tokens boostés.")
    alerts = 0
    for token in boosted[:MAX_BOOSTED_TO_CHECK]:
        alerts += _process_dex_token(
            token, history, current_state, "dex", send_new_token_alert, "dexscreener"
        )
    return alerts


def check_sniper(history, current_state):
    new_tokens = get_latest_new_tokens()
    if not new_tokens:
        print("[sniper] Aucune donnée récupérée.")
        return 0

    print(f"[sniper] {len(new_tokens)} profils neufs.")
    alerts = 0
    for token in new_tokens[:MAX_NEW_TOKENS_TO_CHECK]:
        alerts += _process_dex_token(
            token, history, current_state, "sniper", send_sniper_alert, "sniper"
        )
    return alerts


def run():
    print("=== Scan (Reddit + CoinGecko + DexScreener + Sniper) ===")

    history = load_history()
    current_state = {}

    alerts_sent = 0
    alerts_sent += check_reddit(history, current_state)
    alerts_sent += check_coingecko(history, current_state)
    alerts_sent += check_dexscreener(history, current_state)
    alerts_sent += check_sniper(history, current_state)

    save_scan_result(history, current_state)
    print(f"=== Terminé. {alerts_sent} alerte(s) envoyée(s). ===")


if __name__ == "__main__":
    run()
