"""
Envoie des alertes vers Discord via webhook. Deux formats de
messages, adaptés à ce que chaque source de données peut réellement
mesurer :
- Reddit (comptage de mentions) : garde le format "mentions vs moyenne"
- CoinGecko / DexScreener (classement / présence) : format dédié,
  plus honnête sur ce qui est mesuré.
"""

import os
import requests


def _post_to_discord(message_text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print(f"[discord_alert] DISCORD_WEBHOOK_URL manquant, message affiché en console :\n  {message_text}")
        return

    try:
        response = requests.post(webhook_url, json={"content": message_text}, timeout=10)
        response.raise_for_status()
        print("[discord_alert] Alerte envoyée.")
    except requests.RequestException as e:
        print(f"[discord_alert] Échec de l'envoi Discord : {e}")


def send_alert(coin, current_mentions, average, ratio):
    """Ancien format, pour un vrai comptage de mentions (ex: Reddit)."""
    message = (
        f"🚨 **Pic de mentions détecté : {coin}**\n"
        f"Mentions actuelles : **{current_mentions}**\n"
        f"Moyenne habituelle : {average:.1f}\n"
        f"Ratio : **x{ratio:.1f}**\n"
        f"⚠️ Signal social uniquement — pas un conseil financier."
    )
    _post_to_discord(message)


def send_trending_alert(coin_name, rank, top_n):
    """
    Pour CoinGecko : un coin vient d'entrer dans le classement des
    coins les plus recherchés en ce moment (rank 1 = le plus recherché).
    """
    message = (
        f"📈 **Nouveau coin tendance : {coin_name}**\n"
        f"Il vient d'entrer dans le top {top_n} des coins les plus recherchés sur CoinGecko, "
        f"à la position **#{rank}**.\n"
        f"⚠️ Signal de popularité/recherche uniquement — pas une garantie de hausse de prix, "
        f"pas un conseil financier."
    )
    _post_to_discord(message)


def send_new_token_alert(token_id, chain, description):
    """
    Pour DexScreener : un nouveau token boosté (mis en avant par son
    créateur) vient d'apparaître.
    """
    message = (
        f"🆕 **Nouveau token boosté détecté**\n"
        f"Token : **{token_id}**\n"
        f"Chaîne : {chain}\n"
        f"{description}\n"
        f"⚠️ Un token \"boosté\" veut dire que son créateur a payé pour le mettre en avant — "
        f"ça ne dit rien sur sa fiabilité. Risque élevé de rug pull sur les tokens tout neufs. "
        f"Pas un conseil financier."
    )
    _post_to_discord(message)


def send_sniper_alert(token_id, chain, description):
    """
    Pour un token TOUT JUSTE créé (avant même d'être boosté).
    Le signal le plus rapide, mais aussi le plus risqué.
    """
    message = (
        f"⚡ **[SNIPER] Token flambant neuf détecté**\n"
        f"Token : **{token_id}**\n"
        f"Chaîne : {chain}\n"
        f"{description}\n"
        f"🔴 RISQUE MAXIMUM : ce token vient tout juste d'être créé. La grande majorité des "
        f"tokens à ce stade sont des rug pulls (le créateur part avec l'argent). Aucune "
        f"vérification de fiabilité n'a été faite. Vérifie toi-même (liquidité verrouillée ?, "
        f"contrat renonciable ?, holders ?) avant toute action. Pas un conseil financier."
    )
    _post_to_discord(message)


if __name__ == "__main__":
    # Tests : python discord_alert.py
    send_alert("TESTCOIN", current_mentions=42, average=10.0, ratio=4.2)
    send_trending_alert("XLM", rank=6, top_n=10)
    send_new_token_alert("solana:abcd1234", "solana", "Un token de test")
