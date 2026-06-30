import re
from typing import List, Dict, Any

try:
    from textblob import TextBlob
    _HAS_TEXTBLOB = True
except ImportError:
    _HAS_TEXTBLOB = False

# Weighted crisis keywords categorized by severity tiers
CRISIS_KEYWORDS = {
    # Tier 1: Extreme Crisis (Weight 10)
    "nuclear": 10,
    "war": 10,
    "invasion": 10,
    "cyberattack": 10,
    "pandemic": 10,
    "earthquake": 10,
    "tsunami": 10,
    "default": 10,
    "meltdown": 10,
    "blackout": 10,
    "bioweapon": 10,
    "cyberwarfare": 10,
    
    # Tier 2: Major Crisis (Weight 7)
    "outbreak": 7,
    "explosion": 7,
    "blast": 7,
    "crash": 7,
    "hack": 7,
    "rupture": 7,
    "spill": 7,
    "erupts": 7,
    "sanctions": 7,
    "strike": 7,
    "conflict": 7,
    "clash": 7,
    "hostage": 7,
    "missile": 7,
    "sabotage": 7,
    "emergency": 7,
    "terror": 7,
    
    # Tier 3: Moderate Crisis (Weight 4)
    "fire": 4,
    "flood": 4,
    "storm": 4,
    "warning": 4,
    "shutdown": 4,
    "deficit": 4,
    "disruption": 4,
    "shortage": 4,
    "leak": 4,
    "failure": 4,
    "evacuation": 4,
    "rebellion": 4,
}

FALLBACK_SENTIMENT_SCORES = {
    "positive": [
        "stable", "recovery", "growth", "safe", "calm", "resilient", "contained",
        "progress", "peace", "agreement", "rebound", "surpass", "positive", "strengthens"
    ],
    "negative": [
        "crisis", "risk", "urgent", "danger", "panic", "threat", "volatile", "decline",
        "loss", "emergency", "catastrophe", "critical", "escalate", "warning", "damage"
    ],
}


def get_sentiment_polarity(text: str) -> float:
    """
    Return sentiment polarity from -1.0 (extremely negative) to 1.0 (extremely positive).
    Uses TextBlob NLP pipeline if available, otherwise falls back to a robust keyword classifier.
    """
    normalized = text.strip()
    if not normalized:
        return 0.0
        
    if _HAS_TEXTBLOB:
        try:
            return TextBlob(normalized).sentiment.polarity
        except Exception:
            pass

    # High-quality fallback rule-based sentiment classifier
    normalized_lower = normalized.lower()
    negative_matches = sum(normalized_lower.count(word) for word in FALLBACK_SENTIMENT_SCORES["negative"])
    positive_matches = sum(normalized_lower.count(word) for word in FALLBACK_SENTIMENT_SCORES["positive"])
    
    # Check simple negations ("not safe", "no growth")
    negations = ["not", "no", "never", "hardly", "barely", "isn't", "aren't", "wasn't", "won't"]
    negated = any(re.search(rf"\b{neg}\b\s+\w+", normalized_lower) for neg in negations)
    
    score = positive_matches - negative_matches
    if negated:
        score = -score
        
    if score == 0:
        return 0.0
        
    # Scale score to fall in range [-1.0, 1.0]
    return max(-1.0, min(1.0, score / 3.0))


def _count_keywords(text: str) -> Dict[str, int]:
    """Count occurrences of crisis keywords using boundary-sensitive word matches."""
    found: Dict[str, int] = {}
    normalized_lower = text.lower()
    for keyword in CRISIS_KEYWORDS:
        # Match complete words only to prevent partial matches like 'firmware' matching 'war'
        count = len(re.findall(r"\b" + re.escape(keyword) + r"\b", normalized_lower))
        if count:
            found[keyword] = count
    return found


def calculate_headline_risk(headline: str) -> Dict[str, Any]:
    """
    Evaluate a headline to calculate a crisis risk score from 0 to 100.
    Factors in weighted crisis keyword occurrences, text length adjustments, and NLP sentiment polarity.
    """
    normalized = headline.strip()
    if not normalized:
        return {
            "headline": "",
            "keywords": {},
            "sentiment": 0.0,
            "risk_score": 0.0
        }

    keywords = _count_keywords(normalized)
    
    # Calculate base risk from crisis keyword matches
    keyword_score = sum(CRISIS_KEYWORDS[keyword] * count for keyword, count in keywords.items())
    
    # Fetch headline sentiment
    sentiment = get_sentiment_polarity(normalized)
    
    # Sentiment modifier: Negative sentiment increases risk, while positive sentiment acts as a buffer
    # Max sentiment penalty: +15 risk for highly negative headlines (-1.0 polarity)
    # Min sentiment penalty: -10 risk reduction for highly positive headlines (+1.0 polarity)
    sentiment_modifier = 0.0
    if sentiment < 0:
        sentiment_modifier = abs(sentiment) * 15.0
    elif sentiment > 0:
        sentiment_modifier = -sentiment * 10.0
        
    # Length adjustment: slight weight for descriptive headlines
    length_adjustment = min(3.0, len(normalized) / 100.0)
    
    # Final aggregation: amplify keyword impact and combine modifiers
    raw_score = (keyword_score * 3.5) + sentiment_modifier + length_adjustment
    
    # Restrict output to range [0.0, 100.0]
    risk_score = max(0.0, min(100.0, raw_score))

    return {
        "headline": normalized,
        "keywords": keywords,
        "sentiment": round(sentiment, 3),
        "risk_score": round(risk_score, 1),
    }


def analyze_news_items(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enhance news item dictionary objects by attaching calculated headline risk scores."""
    analyzed: List[Dict[str, Any]] = []
    for item in news_items:
        analysis = calculate_headline_risk(item.get("title", ""))
        enriched = {**item, **analysis}
        analyzed.append(enriched)
    return analyzed


def calculate_crisis_volatility_score(news_items: List[Dict[str, Any]]) -> float:
    """
    Aggregate individual headline risk scores into a single system Crisis Volatility Score (0-100).
    Averages the top 5 highest-scoring headlines to capture black swan shocks without dilution.
    """
    if not news_items:
        return 0.0

    # Sort news items in descending order of risk score
    sorted_items = sorted(news_items, key=lambda x: x.get("risk_score", 0.0), reverse=True)
    
    # Extract the top 5 highest risk headlines
    top_items = sorted_items[:5]
    average_top = sum(item.get("risk_score", 0.0) for item in top_items) / len(top_items)
    
    # Check if there are multiple critical events (risk >= 50) triggering simultaneously
    critical_count = len([item for item in news_items if item.get("risk_score", 0.0) >= 50.0])
    
    # Apply a volume escalator: +5% score increase per concurrent critical headline (capped at +25%)
    escalator = 1.0 + min(0.25, critical_count * 0.05)
    
    final_score = min(100.0, average_top * escalator)
    return round(final_score, 1)
