"""
Enrichit un token DexScreener avec métriques pour le scoring breakout.
"""

import requests
from datetime import datetime, timezone

DEXSCREENER_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/{address}"


def _safe_num(value):
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _pair_age_minutes(pair):
    created = pair.get("pairCreatedAt")
    if not created:
        return None
    created_dt = datetime.fromtimestamp(created / 1000, tz=timezone.utc)
    return (datetime.now(timezone.utc) - created_dt).total_seconds() / 60


def _extract_pair_metrics(pair):
    liquidity = (pair.get("liquidity") or {}).get("usd") or 0
    volume = pair.get("volume") or {}
    txns = pair.get("txns") or {}
    price_change = pair.get("priceChange") or {}
    txns_m5 = txns.get("m5") or {}
    base = pair.get("baseToken") or {}

    buys_m5 = txns_m5.get("buys") or 0
    sells_m5 = txns_m5.get("sells") or 0

    return {
        "symbol": base.get("symbol") or "?",
        "name": base.get("name") or "?",
        "liquidity_usd": liquidity,
        "volume_m5": _safe_num(volume.get("m5")),
        "volume_h1": _safe_num(volume.get("h1")),
        "volume_h24": _safe_num(volume.get("h24")),
        "txns_m5_buys": buys_m5,
        "txns_m5_sells": sells_m5,
        "txns_m5_total": buys_m5 + sells_m5,
        "txns_h1_buys": (txns.get("h1") or {}).get("buys") or 0,
        "txns_h1_sells": (txns.get("h1") or {}).get("sells") or 0,
        "price_change_m5": _safe_num(price_change.get("m5")) if price_change.get("m5") is not None else None,
        "price_change_h1": _safe_num(price_change.get("h1")) if price_change.get("h1") is not None else None,
        "price_usd": pair.get("priceUsd"),
        "market_cap": pair.get("marketCap") or pair.get("fdv"),
        "url": pair.get("url"),
        "pair_created_at": pair.get("pairCreatedAt"),
        "age_minutes": _pair_age_minutes(pair),
    }


def enrich_token(token_address, chain):
    if not token_address:
        return None

    try:
        response = requests.get(
            DEXSCREENER_TOKEN_URL.format(address=token_address),
            timeout=10,
        )
        response.raise_for_status()
        pairs = response.json().get("pairs") or []
    except requests.RequestException as e:
        print(f"[dexscreener_enrich] Erreur pour {token_address[:8]}... : {e}")
        return None

    chain_pairs = [p for p in pairs if p.get("chainId") == chain]
    if not chain_pairs:
        chain_pairs = pairs
    if not chain_pairs:
        return None

    best = max(chain_pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
    metrics = _extract_pair_metrics(best)
    if not metrics.get("url"):
        metrics["url"] = f"https://dexscreener.com/{chain}/{token_address}"
    return metrics
