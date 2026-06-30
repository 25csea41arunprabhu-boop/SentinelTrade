import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
from datetime import datetime, timezone
from typing import List, Dict, Any

from ingestion import DEFAULT_RSS_FEEDS, fetch_market_ticker, fetch_news_feeds
from analyzer import analyze_news_items, calculate_crisis_volatility_score, _HAS_TEXTBLOB
from safeguard import build_safeguard_action

PAGE_TITLE = "SentinelTrade"
DEFAULT_THRESHOLD = 65.0

MONITORED_TICKERS = {
    "S&P 500": "^GSPC",
    "NIFTY 50": "^NSEI",
    "Gold": "GC=F",
}


def format_datetime(value: datetime) -> str:
    """Format datetime objects to a standard clean UTC string."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def inject_custom_styles() -> None:
    """Inject premium CSS styles for a high-end dark-themed glassmorphic UX."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        /* App Background and Font Override */
        .stApp {
            background-color: #0d0f14;
            color: #e2e8f0;
            font-family: 'Outfit', sans-serif;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #111520 !important;
            border-right: 1px solid #1e293b;
        }
        
        /* Header typography adjustment */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            color: #ffffff;
        }
        
        /* Glassmorphic Container Cards */
        .glass-card {
            background: rgba(20, 26, 38, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            margin-bottom: 20px;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        
        .glass-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.12);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.6);
        }
        
        /* Custom Metric card components */
        .metric-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        
        .metric-value {
            font-size: 1.9rem;
            font-weight: 700;
            color: #ffffff;
            margin: 6px 0;
            letter-spacing: -0.02em;
        }
        
        .metric-delta {
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
        }
        
        .delta-up {
            color: #00e676; /* Vibrant Emerald Green */
        }
        
        .delta-down {
            color: #ff1744; /* Bright Emergency Crimson */
        }
        
        /* Badges for News risks */
        .risk-badge {
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-block;
            margin-left: 8px;
        }
        
        .badge-high {
            background-color: rgba(255, 23, 68, 0.12);
            color: #ff5252;
            border: 1px solid rgba(255, 23, 68, 0.35);
        }
        
        .badge-medium {
            background-color: rgba(255, 145, 0, 0.12);
            color: #ffab40;
            border: 1px solid rgba(255, 145, 0, 0.35);
        }
        
        .badge-low {
            background-color: rgba(0, 230, 118, 0.12);
            color: #69f0ae;
            border: 1px solid rgba(0, 230, 118, 0.35);
        }
        
        /* Status Banner Designs */
        .status-banner {
            border-radius: 16px;
            padding: 24px 30px;
            margin-bottom: 25px;
            color: #ffffff;
            position: relative;
            overflow: hidden;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .status-safe {
            background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
            border-left: 8px solid #00e676;
        }
        
        .status-watch {
            background: linear-gradient(135deg, #78350f 0%, #451a03 100%);
            border-left: 8px solid #ffab40;
        }
        
        .status-breached {
            background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
            border-left: 8px solid #ff1744;
            animation: pulse-glow 2.5s infinite alternate;
        }
        
        @keyframes pulse-glow {
            0% {
                box-shadow: 0 0 15px rgba(255, 23, 68, 0.4);
                border-color: rgba(255, 23, 68, 0.2);
            }
            100% {
                box-shadow: 0 0 35px rgba(255, 23, 68, 0.85);
                border-color: rgba(255, 23, 68, 0.6);
            }
        }
        
        /* Interactive Lock Overlay for Trading System */
        .terminal-lock {
            background: rgba(14, 18, 27, 0.95);
            border: 2px dashed #ff1744;
            border-radius: 14px;
            padding: 45px 25px;
            text-align: center;
            margin-top: 15px;
            box-shadow: inset 0 0 20px rgba(255, 23, 68, 0.15);
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 6px 6px 0 0 !important;
            color: #94a3b8 !important;
            padding: 8px 18px !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: rgba(59, 130, 246, 0.2) !important;
            border-color: #3b82f6 !important;
            color: #ffffff !important;
        }
        
        /* Portfolio HTML Table Styling */
        .portfolio-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .portfolio-table th {
            text-align: left;
            padding: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .portfolio-table td {
            padding: 12px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.9rem;
            color: #ffffff;
        }
        
        .portfolio-table tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_status_banner(action: Dict[str, Any], score: float) -> None:
    """Render the main system status banner indicating risk tiers."""
    status = action["status"]
    triggered = action["triggered"]

    if triggered:
        banner_class = "status-breached"
        icon = "🚨"
        subtitle = "CRITICAL SAFEGUARD ACTUATED — TRADING TERMINAL IN LOCK posture"
    elif status == "HEIGHTENED WATCH":
        banner_class = "status-watch"
        icon = "⚠️"
        subtitle = "HEIGHTENED SECURITY SENSITIVITY — MONITORING VOLATILITY TRIGGERS"
    else:
        banner_class = "status-safe"
        icon = "🛡️"
        subtitle = "PORTFOLIO POSTURE SECURE — MONITORING GLOBAL EMERGENCY RSS FEEDS"

    st.markdown(
        f"""
        <div class="status-banner {banner_class}">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                <div>
                    <h1 style="margin: 0; color: #ffffff; font-size: 2.3rem; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                        <span>{icon}</span> SentinelTrade
                    </h1>
                    <div style="font-size: 0.85rem; font-weight: 600; color: rgba(255, 255, 255, 0.8); margin-top: 5px; letter-spacing: 0.05em; text-transform: uppercase;">
                        {subtitle}
                    </div>
                </div>
                <div style="text-align: right; min-width: 150px;">
                    <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.7); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                        Crisis Volatility Index
                    </div>
                    <div style="font-size: 3.2rem; font-weight: 700; color: #ffffff; line-height: 1.0; margin-top: 2px;">
                        {score:.1f}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_cards(ticker_data: Dict[str, Dict[str, Any]]) -> None:
    """Render premium HTML market performance metric cards."""
    cols = st.columns(len(ticker_data))
    for idx, (name, data) in enumerate(ticker_data.items()):
        current = data["current"]
        change = data["change"]
        change_pct = data["change_pct"]
        symbol = data["symbol"]

        delta_class = "delta-up" if change >= 0 else "delta-down"
        arrow = "▲" if change >= 0 else "▼"
        sign = "+" if change >= 0 else ""

        card_html = f"""
        <div class="glass-card" style="margin-bottom: 12px; height: 100%;">
            <div class="metric-title">{name} <span style="font-size: 0.75rem; color: #475569;">({symbol})</span></div>
            <div class="metric-value">${current:,.2f}</div>
            <div class="metric-delta {delta_class}">
                <span style="margin-right: 4px;">{arrow}</span> {sign}{change:,.2f} ({sign}{change_pct}%)
            </div>
            <div style="font-size: 0.65rem; color: #475569; margin-top: 12px;">
                Updated: {format_datetime(data['updated'])}
            </div>
        </div>
        """
        cols[idx].markdown(card_html, unsafe_allow_html=True)


def render_news_feed(news_items: List[Dict[str, Any]]) -> None:
    """Render headlines with color-coded risk assessment metrics."""
    st.markdown("### 📡 Global Crisis Intelligence Feed")
    if not news_items:
        st.info("No headlines found. Connect internet or trigger simulated events.")
        return

    for item in news_items:
        risk_score = item.get("risk_score", 0.0)
        sentiment = item.get("sentiment", 0.0)
        source = item.get("source", "RSS Feed")
        title = item.get("title", "Untitled News Entry")
        summary = item.get("summary", "Summary details unavailable.")
        published_str = format_datetime(item.get("published", datetime.now(timezone.utc)))

        if risk_score >= 65.0:
            badge_html = f'<span class="risk-badge badge-high">High Risk ({risk_score})</span>'
        elif risk_score >= 35.0:
            badge_html = f'<span class="risk-badge badge-medium">Medium Risk ({risk_score})</span>'
        else:
            badge_html = f'<span class="risk-badge badge-low">Low Risk ({risk_score})</span>'

        sentiment_label = f"NLP Polarity: {sentiment:+.2f}"

        st.markdown(
            f"""
            <div class="glass-card" style="padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 0.75rem; color: #3b82f6; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">{source}</span>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <span style="font-size: 0.75rem; color: #64748b;">{sentiment_label}</span>
                        {badge_html}
                    </div>
                </div>
                <h4 style="margin: 8px 0 6px 0; font-size: 0.95rem; line-height: 1.3; font-weight: 600; color: #ffffff;">
                    {title}
                </h4>
                <p style="margin: 0 0 8px 0; font-size: 0.85rem; color: #94a3b8; line-height: 1.45;">
                    {summary}
                </p>
                <div style="font-size: 0.65rem; color: #475569; text-align: right;">
                    {published_str}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def initialize_session_state() -> None:
    """Initialize mock portfolio assets and simulated news records."""
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {
            "SPY": {"shares": 100.0, "name": "S&P 500 ETF", "symbol": "^GSPC"},
            "NSEI": {"shares": 50.0, "name": "NIFTY 50 ETF", "symbol": "^NSEI"},
            "GLD": {"shares": 200.0, "name": "Gold ETF", "symbol": "GC=F"},
            "VIX": {"shares": 0.0, "name": "Volatility Index ETF", "symbol": "^VIX"},
            "CASH": {"shares": 20000.0, "name": "Cash Reserve", "symbol": "CASH"},
        }
    if "injected_headlines" not in st.session_state:
        st.session_state.injected_headlines = []


def main() -> None:
    st.set_page_config(
        page_title="SentinelTrade AI Risk Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_custom_styles()
    initialize_session_state()

    # Define the callback function to commit news and clear the widget state safely
    def inject_headline_callback() -> None:
        typed_headline = st.session_state.get("headline_input_key", "")
        if typed_headline.strip():
            severity = st.session_state.get("severity_slider_key", 75)
            sentiment = st.session_state.get("sentiment_slider_key", -0.6)
            st.session_state.injected_headlines.insert(
                0,
                {
                    "source": "🚨 Sentinel Alert",
                    "title": typed_headline.strip(),
                    "summary": "Geopolitical anomaly manually injected for system simulation.",
                    "published": datetime.now(timezone.utc),
                    "link": "#",
                    "risk_score": float(severity),
                    "sentiment": float(sentiment),
                },
            )
            # Safely clear the text input value in session state before widget re-renders
            st.session_state.headline_input_key = ""
            st.session_state.just_injected = True

    # Sidebar Panel
    with st.sidebar:
        st.markdown("## 🛡️ Risk Parameters")
        st.write("Configure safeguard breaker sensitivities and feed parameters.")

        st.markdown("---")

        data_mode = st.selectbox(
            "Data Stream Source",
            options=["Live Feeds (with Fallbacks)", "Simulated Crisis Mode (Offline)"],
            index=0,
        )
        use_mock = data_mode == "Simulated Crisis Mode (Offline)"

        threshold = st.slider(
            "Circuit Breaker Threshold",
            min_value=10.0,
            max_value=95.0,
            value=DEFAULT_THRESHOLD,
            step=1.0,
            help="Threshold score which triggers emergency asset locks.",
        )

        st.markdown("---")
        st.markdown("### 🚨 Crisis Headline Injector")
        st.write("Manually inject news to simulate black swan anomalies and test breaker response.")

        # Show notification from callback if successful
        if st.session_state.get("just_injected"):
            st.success("Alert injected successfully!")
            st.session_state.just_injected = False

        inj_headline = st.text_input(
            "Crisis Headline Title", 
            placeholder="e.g. Cyberattack hits major oil pipeline...",
            key="headline_input_key"
        )
        inj_severity = st.slider("Crisis Weight", 10, 100, 75, key="severity_slider_key")
        inj_sentiment = st.slider("NLP Polarity Penalty", -1.0, 1.0, -0.6, step=0.1, key="sentiment_slider_key")

        # Use callback for button to clear state before the text_input widget renders again
        st.button(
            "Inject Emergency headline", 
            use_container_width=True, 
            on_click=inject_headline_callback
        )

        if st.session_state.injected_headlines:
            if st.button("Clear Injected Headlines", use_container_width=True):
                st.session_state.injected_headlines = []
                st.success("Cleared custom headlines.")
                st.rerun()

        st.markdown("---")
        st.markdown("### ⚙️ System Diagnostic")
        nlp_status = "TextBlob (NLP Engine)" if _HAS_TEXTBLOB else "Lexicon Rule Fallback"
        st.caption(f"Active NLP Pipeline: `{nlp_status}`")
        if st.button("Reset Mock Portfolio Capital", use_container_width=True):
            st.session_state.portfolio = {
                "SPY": {"shares": 100.0, "name": "S&P 500 ETF", "symbol": "^GSPC"},
                "NSEI": {"shares": 50.0, "name": "NIFTY 50 ETF", "symbol": "^NSEI"},
                "GLD": {"shares": 200.0, "name": "Gold ETF", "symbol": "GC=F"},
                "VIX": {"shares": 0.0, "name": "Volatility Index ETF", "symbol": "^VIX"},
                "CASH": {"shares": 20000.0, "name": "Cash Reserve", "symbol": "CASH"},
            }
            st.success("Portfolio reset successful!")
            st.rerun()

    # Core Data Gathering
    try:
        raw_news = fetch_news_feeds(DEFAULT_RSS_FEEDS, max_items=20, use_mock_only=use_mock)

        # Prepare active news items for calculations
        active_news = []
        
        # 1. Add currently typing temporary headline if present in the text input box
        if inj_headline.strip():
            temp_item = {
                "source": "🚨 Pending Alert",
                "title": inj_headline.strip(),
                "summary": "Draft crisis event currently being evaluated in execution memory.",
                "published": datetime.now(timezone.utc),
                "link": "#",
                "risk_score": float(inj_severity),
                "sentiment": float(inj_sentiment),
            }
            active_news.append(temp_item)
            
        # 2. Add previously committed injected headlines
        active_news.extend(st.session_state.injected_headlines)
        
        # 3. Add standard feeds news
        active_news.extend(raw_news)

        analyzed_news = analyze_news_items(active_news)

        # Ensure custom scores and sentiment settings are preserved for injected/pending items
        for idx, item in enumerate(active_news):
            if idx < len(analyzed_news) and ("risk_score" in item or "sentiment" in item):
                analyzed_news[idx]["risk_score"] = item["risk_score"]
                analyzed_news[idx]["sentiment"] = item["sentiment"]

        score = calculate_crisis_volatility_score(analyzed_news)
        safeguard_action = build_safeguard_action(score, threshold)

        # Pull market quotes
        ticker_data = {}
        for name, symbol in MONITORED_TICKERS.items():
            ticker_data[name] = fetch_market_ticker(symbol, use_mock_only=use_mock)

        # Dynamic VIX Index Quote calculation: scales with Crisis Score
        vix_current = round(15.0 + (score * 0.38) + random.uniform(-0.4, 0.4), 2)
        vix_prev = round(15.0 + (score * 0.32), 2)
        vix_change = round(vix_current - vix_prev, 2)
        vix_change_pct = round((vix_change / vix_prev) * 100.0, 2) if vix_prev > 0 else 0.0

        ticker_data["VIX Index"] = {
            "symbol": "^VIX",
            "current": vix_current,
            "previous": vix_prev,
            "change": vix_change,
            "change_pct": vix_change_pct,
            "updated": datetime.now(timezone.utc),
            "is_mock": True,
        }

        # Render Status Banner at Top
        render_status_banner(safeguard_action, score)

        # Render Market Watch Grid
        render_market_cards(ticker_data)

        # Fetch prices for mock portfolio value evaluation
        prices = {
            "SPY": ticker_data["S&P 500"]["current"],
            "NSEI": ticker_data["NIFTY 50"]["current"],
            "GLD": ticker_data["Gold"]["current"],
            "VIX": ticker_data["VIX Index"]["current"],
            "CASH": 1.0,
        }

        # Calculate Portfolio Metrics
        total_value = 0.0
        portfolio_table_rows = []

        for key, asset in st.session_state.portfolio.items():
            shares = asset["shares"]
            price = prices[key]
            value = shares * price
            total_value += value

        for key, asset in st.session_state.portfolio.items():
            shares = asset["shares"]
            price = prices[key]
            value = shares * price
            allocation = (value / total_value * 100.0) if total_value > 0 else 0.0
            portfolio_table_rows.append(
                {
                    "Key": key,
                    "Name": asset["name"],
                    "Symbol": asset["symbol"],
                    "Shares": shares,
                    "Price": price,
                    "Value": value,
                    "Allocation": allocation,
                }
            )

        # Layout Split: Portfolio Simulation & Advisory Hedges
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown(
                f"""
                <div class="glass-card" style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">
                        <h3 style="margin:0;">💼 Live Simulation Portfolio</h3>
                        <div style="text-align: right;">
                            <span style="font-size:0.75rem; color:#94a3b8; font-weight:600; text-transform:uppercase;">Net Portfolio Capital</span>
                            <div style="font-size:1.7rem; font-weight:700; color:#00e676;">${total_value:,.2f}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Portfolio Holdings Table
            table_body = ""
            for row in portfolio_table_rows:
                if row["Key"] == "CASH":
                    # Cash display detail
                    table_body += (
                        f"<tr>"
                        f"<td><strong>{row['Name']}</strong></td>"
                        f"<td>{row['Symbol']}</td>"
                        f"<td>-</td>"
                        f"<td>-</td>"
                        f"<td>${row['Value']:,.2f}</td>"
                        f"<td><span style='color:#a855f7; font-weight:600;'>{row['Allocation']:.1f}%</span></td>"
                        f"</tr>"
                    )
                else:
                    table_body += (
                        f"<tr>"
                        f"<td><strong>{row['Name']}</strong></td>"
                        f"<td>{row['Symbol']}</td>"
                        f"<td>{row['Shares']:.1f}</td>"
                        f"<td>${row['Price']:,.2f}</td>"
                        f"<td>${row['Value']:,.2f}</td>"
                        f"<td><span style='color:#3b82f6; font-weight:600;'>{row['Allocation']:.1f}%</span></td>"
                        f"</tr>"
                    )

            st.markdown(
                f'<div class="glass-card" style="margin-top: -10px;">'
                f'<table class="portfolio-table">'
                f'<thead>'
                f'<tr>'
                f'<th>Asset Name</th>'
                f'<th>Ticker</th>'
                f'<th>Shares</th>'
                f'<th>Market Price</th>'
                f'<th>Holdings Value</th>'
                f'<th>Weight %</th>'
                f'</tr>'
                f'</thead>'
                f'<tbody>'
                f'{table_body}'
                f'</tbody>'
                f'</table>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Trading Execution Form & Circuit Breaker Logic
            st.markdown("### ⚡ Execution Terminal")
            if safeguard_action["locked"]:
                st.markdown(
                    """
                    <div class="terminal-lock">
                        <span style="font-size: 2.6rem;">🔒</span>
                        <h4 style="color: #ff1744; margin: 12px 0 4px 0; font-weight: 700; letter-spacing: 0.05em;">TERMINAL EXECUTION FROZEN</h4>
                        <p style="color: #94a3b8; font-size: 0.85rem; max-width: 450px; margin: 0 auto 15px auto; line-height: 1.4;">
                            The automatic circuit breaker has disengaged equity purchase actions due to extreme market risk levels. Outer-bound trading is restricted.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("⚡ Trigger Safeguard Portfolio Rebalancing", use_container_width=True):
                    # Reallocate assets to crisis hedge splits: 55% GLD, 20% VIX, 25% CASH, 0% Equities
                    target_gld_val = total_value * 0.55
                    target_vix_val = total_value * 0.20
                    target_cash_val = total_value * 0.25

                    st.session_state.portfolio["SPY"]["shares"] = 0.0
                    st.session_state.portfolio["NSEI"]["shares"] = 0.0
                    st.session_state.portfolio["GLD"]["shares"] = round(target_gld_val / prices["GLD"], 2)
                    st.session_state.portfolio["VIX"]["shares"] = round(target_vix_val / prices["VIX"], 2)
                    st.session_state.portfolio["CASH"]["shares"] = round(target_cash_val, 2)

                    st.success("Defensive safeguard rebalance completed! Equity exposure closed. Capital moved to GLD, VIX, and Cash.")
                    st.rerun()
            else:
                buy_tab, sell_tab = st.tabs(["🛒 Buy Asset Order", "💵 Sell Asset Order"])

                with buy_tab:
                    trade_asset = st.selectbox(
                        "Select Asset to Purchase",
                        options=["SPY", "NSEI", "GLD", "VIX"],
                        format_func=lambda x: f"{st.session_state.portfolio[x]['name']} ({st.session_state.portfolio[x]['symbol']})",
                        key="buy_select",
                    )
                    curr_price = prices[trade_asset]
                    avail_cash = st.session_state.portfolio["CASH"]["shares"]
                    max_shares = avail_cash / curr_price if curr_price > 0 else 0.0

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        buy_qty = st.number_input(
                            "Quantity of Shares",
                            min_value=0.0,
                            max_value=float(max_shares),
                            value=0.0,
                            step=1.0,
                            key="buy_qty_input",
                        )
                    with col_b2:
                        total_cost = buy_qty * curr_price
                        st.metric("Total Cost", f"${total_cost:,.2f}", delta=f"Available Cash: ${avail_cash:,.2f}")

                    if st.button("Submit Buy Order", use_container_width=True):
                        if buy_qty > 0.0 and total_cost <= avail_cash:
                            st.session_state.portfolio[trade_asset]["shares"] += buy_qty
                            st.session_state.portfolio["CASH"]["shares"] -= total_cost
                            st.success(f"Order completed: Bought {buy_qty} shares of {trade_asset}.")
                            st.rerun()

                with sell_tab:
                    sell_asset = st.selectbox(
                        "Select Asset to Liquidate",
                        options=["SPY", "NSEI", "GLD", "VIX"],
                        format_func=lambda x: f"{st.session_state.portfolio[x]['name']} ({st.session_state.portfolio[x]['symbol']})",
                        key="sell_select",
                    )
                    curr_price = prices[sell_asset]
                    owned_shares = st.session_state.portfolio[sell_asset]["shares"]

                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        sell_qty = st.number_input(
                            "Quantity of Shares",
                            min_value=0.0,
                            max_value=float(owned_shares),
                            value=0.0,
                            step=1.0,
                            key="sell_qty_input",
                        )
                    with col_s2:
                        total_proceeds = sell_qty * curr_price
                        st.metric("Total Proceeds", f"${total_proceeds:,.2f}", delta=f"Shares Held: {owned_shares:.1f}")

                    if st.button("Submit Sell Order", use_container_width=True):
                        if sell_qty > 0.0 and sell_qty <= owned_shares:
                            st.session_state.portfolio[sell_asset]["shares"] -= sell_qty
                            st.session_state.portfolio["CASH"]["shares"] += total_proceeds
                            st.success(f"Order completed: Sold {sell_qty} shares of {sell_asset}.")
                            st.rerun()

        with col_right:
            # Advisory safeguarding details card
            st.markdown(
                f"""
                <div class="glass-card">
                    <h3 style="margin-top:0; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">
                        🛡️ AI Safeguard Advisory
                    </h3>
                    <p style="font-size: 0.9rem; line-height: 1.5; color: #e2e8f0; margin-bottom: 15px;">
                        {safeguard_action['advisory']}
                    </p>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px;">
                        Hedge Protection Posture:
                    </div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <span class="risk-badge" style="background: rgba(59,130,246,0.15); color: #3b82f6; border: 1px solid rgba(59,130,246,0.3); font-size: 0.75rem; padding: 6px 12px; margin-left:0;">
                            Circuit Breaker: {'ACTIVE (LOCKED)' if safeguard_action['locked'] else 'INACTIVE (UNLOCKED)'}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Interactive Plotly Pie Chart representing Asset Allocation
            alloc_labels = [row["Name"] for row in portfolio_table_rows if row["Value"] > 0]
            alloc_values = [row["Value"] for row in portfolio_table_rows if row["Value"] > 0]

            if alloc_values:
                # Harmonious color palette matching dark glass theme
                alloc_colors = ["#3b82f6", "#10b981", "#fbbf24", "#ef4444", "#94a3b8"]
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=alloc_labels,
                            values=alloc_values,
                            hole=0.45,
                            marker=dict(colors=alloc_colors, line=dict(color="#0d0f14", width=2)),
                            textinfo="percent",
                            hoverinfo="label+value",
                        )
                    ]
                )
                fig.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.35,
                        xanchor="center",
                        x=0.5,
                        font=dict(color="#94a3b8", size=10),
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=240,
                    font=dict(color="#e2e8f0", family="Outfit, sans-serif"),
                )

                st.markdown(
                    """
                    <div class="glass-card" style="margin-top: -5px;">
                        <h4 style="margin-top:0; margin-bottom: 12px; text-align: center;">Target Exposure Mix</h4>
                    """,
                    unsafe_allow_html=True,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        # Bottom Row: News headlines stream
        render_news_feed(analyzed_news)

    except Exception as exc:
        st.error(f"The dashboard encountered an error loading live components: {exc}")
        st.stop()


if __name__ == "__main__":
    main()
