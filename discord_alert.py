"""
Envoie des alertes Discord via webhook (embeds riches avec liens).
"""

import os
import requests


def _post_to_discord(content=None, embed=None):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    payload = {}
    if content:
        payload["content"] = content
    if embed:
        payload["embeds"] = [embed]

    if not webhook_url:
        print(f"[discord_alert] DISCORD_WEBHOOK_URL manquant, message affiché en console :\n  {payload}")
        return

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("[discord_alert] Alerte envoyée.")
    except requests.RequestException as e:
        print(f"[discord_alert] Échec de l'envoi Discord : {e}")


def _footer():
    return {"text": "Signal informatif — pas un conseil financier"}


def _score_color(score):
    if score >= 75:
        return 0x00CC66
    if score >= 60:
        return 0xFFD700
    return 0xFF8800


def _score_fields(score, reasons):
    fields = [{"name": "Score breakout", "value": f"**{score}/100**", "inline": True}]
    if reasons:
        fields.append({
            "name": "Pourquoi",
            "value": "\n".join(f"• {r}" for r in reasons[:4]),
            "inline": False,
        })
    return fields


def _token_fields(chain, enriched, score, reasons):
    fields = [{"name": "Chaîne", "value": chain, "inline": True}]
    fields.extend(_score_fields(score, reasons))
    if enriched:
        if enriched.get("liquidity_usd") is not None:
            fields.append({"name": "Liquidité", "value": f"${enriched['liquidity_usd']:,.0f}", "inline": True})
        if enriched.get("volume_h1"):
            fields.append({"name": "Volume 1h", "value": f"${enriched['volume_h1']:,.0f}", "inline": True})
        buys = enriched.get("txns_m5_buys") or 0
        sells = enriched.get("txns_m5_sells") or 0
        if buys + sells:
            ratio = buys / (buys + sells)
            fields.append({"name": "Achats 5min", "value": f"{ratio:.0%}", "inline": True})
    return fields


def send_alert(coin, current_mentions, average, ratio):
    embed = {
        "title": f"🚨 Pic de mentions : {coin}",
        "color": 0xFF4444,
        "fields": [
            {"name": "Mentions actuelles", "value": str(current_mentions), "inline": True},
            {"name": "Moyenne habituelle", "value": f"{average:.1f}", "inline": True},
            {"name": "Ratio", "value": f"x{ratio:.1f}", "inline": True},
        ],
        "footer": _footer(),
    }
    _post_to_discord(embed=embed)


def send_trending_alert(coin_name, rank, top_n, previous_rank=None):
    fields = [
        {"name": "Position", "value": f"#{rank} / top {top_n}", "inline": True},
    ]
    if previous_rank is not None:
        fields.append({"name": "Avant", "value": f"#{previous_rank}", "inline": True})
        fields.append({"name": "Progression", "value": f"+{previous_rank - rank} places", "inline": True})

    embed = {
        "title": f"📈 Tendance CoinGecko : {coin_name}",
        "description": (
            f"**{coin_name}** est dans le top {top_n} des coins les plus recherchés sur CoinGecko."
        ),
        "color": 0xFFD700,
        "fields": fields,
        "url": f"https://www.coingecko.com/fr/pièces/{coin_name.lower()}",
        "footer": _footer(),
    }
    _post_to_discord(embed=embed)


def send_new_token_alert(
    token_id, chain, description, symbol=None, url=None, score=None, reasons=None, enriched=None,
):
    title = f"🆕 Token boosté : {symbol or token_id[:16]}"
    embed = {
        "title": title,
        "description": description or "Token boosté sur DexScreener.",
        "color": _score_color(score or 0),
        "fields": _token_fields(chain, enriched, score, reasons),
        "footer": _footer(),
    }
    if url:
        embed["url"] = url
    _post_to_discord(embed=embed)


def send_sniper_alert(
    token_id, chain, description, symbol=None, url=None, score=None, reasons=None, enriched=None,
):
    title = f"⚡ [SNIPER] {symbol or token_id[:16]}"
    embed = {
        "title": title,
        "description": (
            (description or "Token flambant neuf détecté.")
            + "\n\n🔴 **RISQUE ÉLEVÉ** — vérifie liquidité, holders et contrat avant toute action."
        ),
        "color": _score_color(score or 0),
        "fields": _token_fields(chain, enriched, score, reasons),
        "footer": _footer(),
    }
    if url:
        embed["url"] = url
    _post_to_discord(embed=embed)


def send_pump_alert(name, symbol, mint, sol_amount, url, score=None, reasons=None, enriched=None):
    fields = [
        {"name": "Lancement", "value": f"{sol_amount:.2f} SOL", "inline": True},
        {"name": "Mint", "value": f"`{mint}`", "inline": False},
    ]
    if score is not None:
        fields = _score_fields(score, reasons) + fields
        if enriched and enriched.get("liquidity_usd"):
            fields.insert(2, {
                "name": "Liquidité",
                "value": f"${enriched['liquidity_usd']:,.0f}",
                "inline": True,
            })

    embed = {
        "title": f"🔥 Pump.fun : {name} ({symbol})",
        "description": "Memecoin pump.fun avec signaux breakout détectés.",
        "color": _score_color(score or 0),
        "fields": fields,
        "url": url,
        "footer": _footer(),
    }
    _post_to_discord(embed=embed)
