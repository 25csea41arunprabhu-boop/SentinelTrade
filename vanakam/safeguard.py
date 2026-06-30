from typing import Dict, List, Any


def check_circuit_breaker(score: float, threshold: float) -> bool:
    """Evaluate whether the crisis score has crossed the safeguard threshold."""
    return score >= threshold


def recommend_hedge_assets(score: float) -> List[str]:
    """Provide a flat list of hedging assets recommended for the current risk tier."""
    if score < 35.0:
        return ["S&P 500 Index ETF", "NIFTY 50 Index ETF", "Corporate Bonds"]
    if score < 65.0:
        return ["Gold ETF", "US Treasury Bills", "Inverse Equity Funds"]
    return ["Physical Gold ETF", "VIX Volatility Index ETF", "Ultra-Short Cash Reserves"]


def get_hedging_allocations(score: float) -> Dict[str, float]:
    """
    Return percentage allocations across assets based on crisis severity.
    Dynamically routes capital from risky equities to defensive hedges and cash.
    """
    # Safe State
    if score < 35.0:
        return {
            "S&P 500 ETF (SPY)": 60.0,
            "NIFTY 50 ETF": 25.0,
            "Gold ETF (GLD)": 10.0,
            "Cash / T-Bills": 5.0,
            "Volatility ETF (VIX)": 0.0,
        }
    # Heightened Watch State
    if score < 65.0:
        return {
            "S&P 500 ETF (SPY)": 35.0,
            "NIFTY 50 ETF": 15.0,
            "Gold ETF (GLD)": 30.0,
            "Cash / T-Bills": 15.0,
            "Volatility ETF (VIX)": 5.0,
        }
    # Breached Circuit Breaker State (Risk >= 65)
    # Equities are frozen/sold, funds are parked entirely in hedges and liquid cash
    return {
        "S&P 500 ETF (SPY)": 0.0,
        "NIFTY 50 ETF": 0.0,
        "Gold ETF (GLD)": 55.0,
        "Cash / T-Bills": 25.0,
        "Volatility ETF (VIX)": 20.0,
    }


def build_safeguard_action(score: float, threshold: float) -> Dict[str, Any]:
    """
    Construct a complete advisory action and portfolio posture based on risk metrics.
    Returns status indicators, advisory texts, lock state, and recommended target allocations.
    """
    is_triggered = check_circuit_breaker(score, threshold)
    
    if is_triggered:
        status = "CRISIS RISK DETECTED"
        advisory = (
            "⚠️ CIRCUIT BREAKER TRIGGERED! Portfolio locking mechanism is engaged. "
            "Mock trading features are frozen. Defensive capital preservation protocol has been activated. "
            "We recommend immediate reallocation of equity assets into physical gold, volatility index hedges, and highly liquid cash reserves."
        )
    elif score >= (threshold * 0.70):
        status = "HEIGHTENED WATCH"
        advisory = (
            "🔍 RISK PROFILE ELEVATED. Volatility markers are rising. "
            "Normal trading operations are active, but we advise reducing equity leverage "
            "and scaling up gold hedges in preparation for a potential portfolio lock."
        )
    else:
        status = "MARKET SAFE"
        advisory = (
            "✅ CONDITIONS STANDARD. Global risk parameters remain within historical bounds. "
            "Automated protective armor is in passive monitoring mode. "
            "Maintain baseline equity exposures and standard asset allocations."
        )

    return {
        "status": status,
        "triggered": is_triggered,
        "advisory": advisory,
        "recommended_hedges": recommend_hedge_assets(score),
        "allocations": get_hedging_allocations(score),
        "locked": is_triggered,
    }
