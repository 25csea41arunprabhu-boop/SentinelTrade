import feedparser
import yfinance as yf
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# A list of reliable RSS feeds for world news and business alerts
DEFAULT_RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=crisis%20disaster%20cyberattack%20war%20earthquake&sort=date",
]

# Authentic mock news archives to use as a fallback if feeds fail or are blocked
MOCK_CRISIS_HEADLINES = [
    {
        "source": "Reuters (Simulated)",
        "title": "Geopolitical escalation reported: Strategic missile drills commence near eastern border",
        "summary": "Regional forces placed on high alert as borders see military reinforcement. Equity futures slide.",
    },
    {
        "source": "Bloomberg (Simulated)",
        "title": "Severe cyberattack halts critical banking systems and clearinghouses across Europe",
        "summary": "Financial authorities report coordinates outages. Tech companies scramble to patch vulnerabilities.",
    },
    {
        "source": "BBC News (Simulated)",
        "title": "Magnitude 7.4 earthquake strikes major semiconductor manufacturing hub",
        "summary": "Production lines halted. Early reports indicate significant structural impact to silicon factories.",
    },
    {
        "source": "AP News (Simulated)",
        "title": "Explosion shuts down key shipping channel; oil tanker routes suspended",
        "summary": "Maritime transport authorities verify a terminal explosion. Energy spot prices spike by 6%.",
    },
    {
        "source": "CNBC (Simulated)",
        "title": "Sovereign debt default contagion fears rise as bond yield rates double",
        "summary": "Emergency talks held behind closed doors. Central banks announce joint liquidity support action.",
    },
    {
        "source": "Global Health Watch (Simulated)",
        "title": "New highly transmissible respiratory outbreak triggers quarantine in transportation hubs",
        "summary": "Aviation sectors brace for travel restrictions. Stocks of airline conglomerates slide 8%.",
    },
    {
        "source": "Energy Intelligence (Simulated)",
        "title": "Major oil refinery offline following electrical grid failure caused by heatwave",
        "summary": "Grid operator declares emergency status as reserve margins thin out during peak summer demand.",
    },
    {
        "source": "Reuters (Simulated)",
        "title": "Unprecedented pipeline leak forces emergency evacuation of refining terminal",
        "summary": "Environmental agencies inspect the site. Flow rates halted on major continental distribution line.",
    },
]

MOCK_SAFE_HEADLINES = [
    {
        "source": "Bloomberg (Simulated)",
        "title": "Global markets stabilize as consumer price index reflects cooling inflation",
        "summary": "Monetary policy committees signal potential rate cuts, fueling positive market sentiment.",
    },
    {
        "source": "TechCrunch (Simulated)",
        "title": "Next-generation energy-efficient microchips unveiled for artificial intelligence workloads",
        "summary": "New architecture reduces power utilization by 40% while doubling inference speeds.",
    },
    {
        "source": "CNBC (Simulated)",
        "title": "Retail sales surpass forecasts, demonstrating resilient consumer spending power",
        "summary": "Strong employment figures continue to bolster household purchasing power across major sectors.",
    },
    {
        "source": "BBC News (Simulated)",
        "title": "Global supply chain congestions fall to lowest levels in three years",
        "summary": "Shipping freight rates normalize as port bottlenecks clear up, easing retail inventory pressures.",
    },
]

MOCK_TICKER_BASE_PRICES = {
    "^GSPC": {"current": 5450.0, "change_direction": -0.2},  # S&P 500
    "^NSEI": {"current": 23550.0, "change_direction": -0.15}, # NIFTY 50
    "GC=F": {"current": 2340.0, "change_direction": 1.2},    # Gold Futures
}


def _parse_entry_date(entry: Dict[str, Any]) -> datetime:
    """Safely parse publishing date from an RSS feed entry, returning UTC datetime."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published is None:
        return datetime.now(timezone.utc)
    try:
        # parsed_time is structured time tuple (tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, ...)
        dt = datetime(
            year=published[0],
            month=published[1],
            day=published[2],
            hour=published[3],
            minute=published[4],
            second=published[5],
            tzinfo=timezone.utc,
        )
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def fetch_news_feeds(feed_urls: List[str] = None, max_items: int = 25, use_mock_only: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch live headlines from global news RSS feeds.
    Falls back to high-fidelity mock data if feeds fail, are empty, or if offline mode is requested.
    """
    if use_mock_only:
        return _get_mock_headlines(max_items)

    feed_urls = feed_urls or DEFAULT_RSS_FEEDS
    headlines: List[Dict[str, Any]] = []

    for source_url in feed_urls:
        try:
            parsed = feedparser.parse(source_url)
            # If the parser failed or returned an empty feed, move on
            if parsed.bozo or not parsed.entries:
                continue

            for entry in parsed.entries:
                published_at = _parse_entry_date(entry)
                headlines.append(
                    {
                        "source": parsed.feed.get("title", "World News Channel"),
                        "title": entry.get("title", "Untitled News Alert").strip(),
                        "summary": entry.get("summary", "").strip(),
                        "link": entry.get("link", "#"),
                        "published": published_at,
                    }
                )
        except Exception:
            continue

    # If no live headlines were successfully retrieved, fall back to mock headlines
    if not headlines:
        return _get_mock_headlines(max_items)

    # Sort feeds by descending publication date
    headlines.sort(key=lambda item: item["published"], reverse=True)
    return headlines[:max_items]


def _get_mock_headlines(max_items: int = 25) -> List[Dict[str, Any]]:
    """Generate structured mock headlines with fresh simulated timestamps."""
    headlines = []
    now = datetime.now(timezone.utc)
    
    # Mix crisis and safe headlines to give a balanced realistic feed
    raw_pool = MOCK_CRISIS_HEADLINES + MOCK_SAFE_HEADLINES
    
    # Ensure variety by shuffling or sorting
    for idx, item in enumerate(raw_pool):
        # Create timestamps spread across the last 24 hours
        minutes_ago = idx * 45 + random.randint(5, 20)
        pub_date = now - timedelta(minutes=minutes_ago)
        
        headlines.append({
            "source": item["source"],
            "title": item["title"],
            "summary": item["summary"],
            "link": "#",
            "published": pub_date
        })
        
    headlines.sort(key=lambda item: item["published"], reverse=True)
    return headlines[:max_items]


def fetch_market_ticker(symbol: str, use_mock_only: bool = False) -> Dict[str, Any]:
    """
    Fetch price and daily trend statistics for a market ticker symbol using yfinance.
    Provides realistic floating simulation as a robust fallback.
    """
    if use_mock_only:
        return _get_mock_ticker(symbol)

    try:
        ticker = yf.Ticker(symbol)
        # Fetching a small window of history to calculate the current price and change
        history = ticker.history(period="3d", interval="1d")
        if history.empty or len(history) < 2:
            raise ValueError(f"Insufficient history returned for {symbol}")

        latest = history.iloc[-1]
        previous = history.iloc[-2]

        current_price = float(latest["Close"])
        prior_price = float(previous["Close"])
        change = current_price - prior_price
        change_pct = (change / prior_price) * 100 if prior_price != 0 else 0.0

        return {
            "symbol": symbol,
            "current": round(current_price, 2),
            "previous": round(prior_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "updated": datetime.now(timezone.utc),
            "is_mock": False
        }
    except Exception:
        # Fall back to simulated prices if Yahoo Finance fails or goes offline
        return _get_mock_ticker(symbol)


def _get_mock_ticker(symbol: str) -> Dict[str, Any]:
    """Generate a realistic mock ticker quote with random fluctuation."""
    base_info = MOCK_TICKER_BASE_PRICES.get(symbol, {"current": 100.0, "change_direction": 0.0})
    base_price = base_info["current"]
    
    # Introduce small random daily fluctuation (-1.5% to +1.5%)
    fluctuation = random.uniform(-1.5, 1.5)
    # Add a slight bias based on "change_direction" (e.g. gold goes up, equities go down during crisis checks)
    fluctuation += base_info["change_direction"]
    
    change_pct = round(fluctuation, 2)
    change = round((base_price * change_pct) / 100.0, 2)
    current_price = round(base_price + change, 2)
    previous_price = round(base_price, 2)

    return {
        "symbol": symbol,
        "current": current_price,
        "previous": previous_price,
        "change": change,
        "change_pct": change_pct,
        "updated": datetime.now(timezone.utc),
        "is_mock": True
    }
