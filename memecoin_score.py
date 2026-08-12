"""
Score les memecoins selon leur potentiel de "percée".
Combine liquidité, activité, pression acheteuse et momentum.
"""

from config import (
    IDEAL_LIQUIDITY_MAX,
    IDEAL_LIQUIDITY_MIN,
    MAX_LIQUIDITY_USD,
    MAX_TOKEN_AGE_MINUTES,
    MIN_BREAKOUT_SCORE,
    MIN_BUY_RATIO,
    MIN_HIGH_CONVICTION_SCORE,
    MIN_LIQUIDITY_USD,
    MIN_TXNS_M5,
)


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _score_liquidity(liquidity_usd):
    if liquidity_usd < MIN_LIQUIDITY_USD:
        return 0, f"liquidité trop faible (${liquidity_usd:,.0f})"
    if liquidity_usd > MAX_LIQUIDITY_USD:
        return 0, f"déjà trop gros (${liquidity_usd:,.0f}) — fenêtre manquée"

    if IDEAL_LIQUIDITY_MIN <= liquidity_usd <= IDEAL_LIQUIDITY_MAX:
        return 22, f"liquidité idéale (${liquidity_usd:,.0f})"

    if liquidity_usd < IDEAL_LIQUIDITY_MIN:
        ratio = liquidity_usd / IDEAL_LIQUIDITY_MIN
        return int(10 + 8 * ratio), f"liquidité correcte (${liquidity_usd:,.0f})"

    overflow = (liquidity_usd - IDEAL_LIQUIDITY_MAX) / (MAX_LIQUIDITY_USD - IDEAL_LIQUIDITY_MAX)
    return int(18 - 10 * overflow), f"liquidité élevée (${liquidity_usd:,.0f})"


def _score_volume_activity(enriched):
    liquidity = enriched.get("liquidity_usd") or 1
    vol_m5 = enriched.get("volume_m5") or 0
    vol_h1 = enriched.get("volume_h1") or 0
    txns_m5 = enriched.get("txns_m5_total") or 0

    if txns_m5 < MIN_TXNS_M5:
        return 0, f"peu d'activité ({txns_m5} txns / 5 min)"

    turnover_m5 = vol_m5 / liquidity
    turnover_h1 = vol_h1 / liquidity

    score = 0
    reasons = []

    if turnover_m5 >= 0.15:
        score += 14
        reasons.append(f"volume 5min chaud (x{turnover_m5:.2f} vs liquidité)")
    elif turnover_m5 >= 0.05:
        score += 8
        reasons.append(f"volume 5min actif (x{turnover_m5:.2f})")
    else:
        score += 3
        reasons.append("volume 5min faible")

    if turnover_h1 >= 0.5:
        score += 8
        reasons.append(f"volume 1h solide (x{turnover_h1:.2f})")
    elif turnover_h1 >= 0.2:
        score += 4

    return _clamp(score, 0, 22), " · ".join(reasons)


def _score_buy_pressure(enriched):
    buys = enriched.get("txns_m5_buys") or 0
    sells = enriched.get("txns_m5_sells") or 0
    total = buys + sells

    if total < MIN_TXNS_M5:
        return 0, "pas assez de trades pour mesurer la pression"

    ratio = buys / total
    if ratio < MIN_BUY_RATIO:
        return 0, f"plus de ventes ({ratio:.0%} achats)"

    if ratio >= 0.68:
        return 22, f"forte pression acheteuse ({ratio:.0%} achats / 5 min)"
    if ratio >= 0.58:
        return 16, f"pression acheteuse ({ratio:.0%} achats / 5 min)"
    return 10, f"légère pression acheteuse ({ratio:.0%} achats / 5 min)"


def _score_momentum(enriched):
    change_m5 = enriched.get("price_change_m5")
    change_h1 = enriched.get("price_change_h1")
    score = 0
    parts = []

    if change_m5 is not None:
        if change_m5 >= 25:
            score += 12
            parts.append(f"+{change_m5:.0f}% / 5 min")
        elif change_m5 >= 8:
            score += 8
            parts.append(f"+{change_m5:.0f}% / 5 min")
        elif change_m5 >= 0:
            score += 4
            parts.append(f"+{change_m5:.0f}% / 5 min")
        else:
            return 0, f"momentum négatif ({change_m5:.0f}% / 5 min)"

    if change_h1 is not None and change_h1 >= 15:
        score += 6
        parts.append(f"+{change_h1:.0f}% / 1h")

    if not parts:
        return 4, "momentum neutre (données limitées)"

    return _clamp(score, 0, 18), " · ".join(parts)


def _score_freshness(enriched):
    age = enriched.get("age_minutes")
    if age is None:
        return 6, "âge inconnu"

    if age <= 30:
        return 12, f"très récent ({age:.0f} min)"
    if age <= 90:
        return 9, f"récent ({age:.0f} min)"
    if age <= MAX_TOKEN_AGE_MINUTES:
        return 5, f"encore jeune ({age:.0f} min)"

    return 0, f"trop vieux ({age:.0f} min) — fenêtre early passée"


def _score_pump_conviction(initial_sol):
    if initial_sol is None:
        return 0, None

    if initial_sol >= 8:
        return 10, f"gros lancement ({initial_sol:.1f} SOL)"
    if initial_sol >= 4:
        return 7, f"lancement solide ({initial_sol:.1f} SOL)"
    if initial_sol >= 2:
        return 4, f"lancement correct ({initial_sol:.1f} SOL)"
    return 0, f"lancement faible ({initial_sol:.1f} SOL)"


def _score_boosted(is_boosted):
    if is_boosted:
        return 4, "boosté (visibilité payée)"
    return 0, None


def _is_spam_symbol(enriched):
    symbol = (enriched.get("symbol") or "").upper()
    name = (enriched.get("name") or "").lower()

    spam_symbols = {"TEST", "SCAM", "RUG", "AAA", "XXX"}
    if symbol in spam_symbols:
        return True
    if len(symbol) > 12 or len(name) > 40:
        return True
    if name in {"test", "test token", "new token"}:
        return True
    return False


def _score_community(metadata):
    """
    Score basé sur la présence de réseaux sociaux, une description et une
    image — proxy pour la "communauté" d'un token. Un token pump.fun sans
    aucun réseau social lié a très rarement une communauté active.

    Retourne (points, reason, has_social).
    """
    if not metadata:
        return 0, "aucune métadonnée récupérée (image/réseaux inconnus)", False

    socials = [k for k in ("twitter", "telegram", "website") if metadata.get(k)]
    has_social = len(socials) > 0

    points = {0: 0, 1: 5, 2: 10, 3: 14}.get(len(socials), 14)

    description = (metadata.get("description") or "").strip()
    image = (metadata.get("image") or "").strip()

    if 15 <= len(description) <= 300:
        points += 3
    if image:
        points += 2

    if not socials:
        reason = "aucun réseau social lié (twitter/telegram/site) — communauté quasi inexistante"
    else:
        reason = f"communauté visible ({', '.join(socials)})"

    return _clamp(points, 0, 19), reason, has_social


def _score_narrative(name, symbol, description, trending_keywords):
    """
    Bonus si le nom/symbole/description du token colle à une tendance
    déjà détectée (CoinGecko trending, coins suivis en config). Les
    tokens qui surfent sur une narrative déjà virale ont historiquement
    plus de chances d'attirer l'attention rapidement.
    """
    if not trending_keywords:
        return 0, None

    text = f"{name or ''} {symbol or ''} {description or ''}".lower()
    matches = sorted({kw for kw in trending_keywords if kw and kw.lower() in text})

    if not matches:
        return 0, None

    points = _clamp(6 * len(matches), 0, 15)
    return points, f"nom aligné avec une tendance actuelle ({', '.join(matches[:3])})"


def score_memecoin_strict(enriched, *, initial_sol=None, metadata=None, name=None, symbol=None, trending_keywords=None):
    """
    Version renforcée du scoring, réservée au sniper pump.fun ("forte
    conviction"). Combine le score technique habituel (liquidité, volume,
    pression acheteuse, momentum, fraîcheur) avec des signaux de
    communauté et de narrative.

    Différence clé avec score_memecoin() : l'ABSENCE TOTALE de réseau
    social (pas de twitter/telegram/site) est éliminatoire ici. Un token
    sans aucune présence sociale a statistiquement très peu de chances de
    devenir viral, quels que soient ses chiffres de marché.

    ⚠️ IMPORTANT : même un score de 100/100 ne garantit AUCUN gain futur,
    et encore moins un x2 ou x3. C'est un filtre de probabilité basé sur
    des patterns observés (liquidité saine, pression acheteuse réelle,
    communauté visible, narrative porteuse) — pas une prédiction fiable.
    Le marché memecoin reste extrêmement volatile, manipulable (wash
    trading, bots, rugs) et imprévisible. Utilise ça comme un filtre pour
    réduire le bruit, jamais comme un signal d'achat automatique.
    """
    base_score, base_reasons, base_passed = score_memecoin(
        enriched, initial_sol=initial_sol, is_boosted=False
    )

    if base_score == 0:
        return 0, base_reasons, False

    community_points, community_reason, has_social = _score_community(metadata)
    description = (metadata or {}).get("description", "")
    narrative_points, narrative_reason = _score_narrative(name, symbol, description, trending_keywords)

    reasons = list(base_reasons)
    if community_reason:
        reasons.append(community_reason)
    if narrative_reason:
        reasons.append(narrative_reason)

    total = _clamp(base_score + community_points + narrative_points, 0, 100)
    passed = base_passed and has_social and total >= MIN_HIGH_CONVICTION_SCORE

    return total, reasons, passed


def score_memecoin(enriched, *, initial_sol=None, is_boosted=False):
    """
    Retourne (score 0-100, reasons list, passed bool).
    passed = score >= MIN_BREAKOUT_SCORE et aucun critère éliminatoire.
    """
    if not enriched:
        return 0, ["pas de données DexScreener"], False

    if _is_spam_symbol(enriched):
        return 0, ["symbole/nom suspect (spam)"], False

    reasons = []
    total = 0
    hard_fail = False

    for scorer, args in (
        (_score_liquidity, (enriched.get("liquidity_usd") or 0,)),
        (_score_volume_activity, (enriched,)),
        (_score_buy_pressure, (enriched,)),
        (_score_momentum, (enriched,)),
        (_score_freshness, (enriched,)),
    ):
        pts, reason = scorer(*args)
        total += pts
        if reason:
            reasons.append(reason)
        if pts == 0 and scorer in (_score_liquidity, _score_buy_pressure, _score_momentum, _score_freshness):
            hard_fail = True

    pts, reason = _score_pump_conviction(initial_sol)
    total += pts
    if reason:
        reasons.append(reason)

    pts, reason = _score_boosted(is_boosted)
    total += pts
    if reason:
        reasons.append(reason)

    score = _clamp(total, 0, 100)
    passed = score >= MIN_BREAKOUT_SCORE and not hard_fail
    return score, reasons, passed
