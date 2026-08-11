"""
Envoie une alerte dans un salon Discord via un webhook.
Un webhook Discord est une simple URL : on lui envoie du JSON en
POST, et le message apparaît dans le salon. Gratuit, pas de bot à
héberger. Voir README.md étape 3 pour créer ce webhook.
"""

import os
import requests


def send_alert(coin, current_mentions, average, ratio):
    """Envoie un message formaté dans Discord."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("[discord_alert] DISCORD_WEBHOOK_URL manquant, alerte affichée en console seulement :")
        print(f"  🚨 {coin} : {current_mentions} mentions (x{ratio:.1f} vs moyenne {average:.1f})")
        return

    message = {
        "content": (
            f"🚨 **Pic de mentions détecté : {coin}**\n"
            f"Mentions actuelles : **{current_mentions}**\n"
            f"Moyenne habituelle : {average:.1f}\n"
            f"Ratio : **x{ratio:.1f}**\n"
            f"⚠️ Signal social uniquement — vérifie toujours avant d'agir, "
            f"ce n'est pas un conseil financier."
        )
    }

    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print(f"[discord_alert] Alerte envoyée pour {coin}.")
    except requests.RequestException as e:
        print(f"[discord_alert] Échec de l'envoi Discord : {e}")


if __name__ == "__main__":
    # Test : python discord_alert.py (nécessite DISCORD_WEBHOOK_URL dans l'environnement)
    send_alert("TESTCOIN", current_mentions=42, average=10.0, ratio=4.2)
