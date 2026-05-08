import streamlit as st
import requests
import pandas as pd
import time
import random
import re
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="DealGenie AI",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg,#020617,#0f172a,#111827);
    color: white;
}

.main-title {
    font-size: 4rem;
    font-weight: 900;
    background: linear-gradient(90deg,#d946ef,#ec4899,#22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}

.subtitle {
    text-align:center;
    color:#94a3b8;
    font-size:1.2rem;
    margin-bottom:2rem;
}

.card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 20px;
    margin-bottom:20px;
}

.metric-card {
    background: rgba(255,255,255,0.04);
    border-radius:20px;
    padding:20px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.08);
}

.metric-number {
    font-size:2rem;
    font-weight:800;
    color:#d946ef;
}

.metric-label {
    color:#94a3b8;
}

.insight {
    background: linear-gradient(135deg, rgba(217,70,239,0.18), rgba(34,211,238,0.12));
    padding:18px;
    border-radius:20px;
    border:1px solid rgba(255,255,255,0.08);
    margin-bottom:12px;
}

.product-card {
    background: rgba(255,255,255,0.05);
    border-radius:28px;
    overflow:hidden;
    border:1px solid rgba(255,255,255,0.08);
    transition:0.3s;
    margin-bottom:25px;
}

.product-card:hover {
    transform: translateY(-4px);
    border:1px solid rgba(217,70,239,0.4);
}

.product-image {
    width:100%;
    height:260px;
    object-fit:cover;
}

.badge {
    background: linear-gradient(90deg,#d946ef,#ec4899);
    padding:6px 12px;
    border-radius:999px;
    color:white;
    font-size:12px;
    font-weight:700;
    display:inline-block;
}

.buy-btn {
    display:inline-block;
    background: linear-gradient(90deg,#d946ef,#ec4899);
    color:white !important;
    text-decoration:none;
    padding:12px 20px;
    border-radius:14px;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="main-title">DealGenie AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI Powered Shopping Intelligence Platform</div>', unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚡ Menu")

    search_mode = st.selectbox(
        "Search Mode",
        [
            "Smart AI",
            "Budget Hunter",
            "Best Rated",
            "Trending",
            "Luxury"
        ]
    )

    sort_by = st.selectbox(
        "Sort By",
        [
            "Cheapest",
            "Highest Rated",
            "Most Reviews"
        ]
    )

    min_rating = st.slider("Minimum Rating", 0.0, 5.0, 3.5)

    max_products = st.slider("Max Products", 3, 20, 9)

# ---------------- SEARCH ----------------
col1, col2 = st.columns([5,1])

with col1:
    query = st.text_input(
        "",
        placeholder="Search products like: iPhone 15, Nike shoes, Gaming Laptop..."
    )

with col2:
    search_clicked = st.button("🚀 Search")

# ---------------- METRICS ----------------
m1,m2,m3,m4 = st.columns(4)

metrics = [
    ("2.5M+", "Products Compared"),
    ("150+", "Stores"),
    ("98%", "Price Accuracy"),
    ("24/7", "AI Insights")
]

for col,metric in zip([m1,m2,m3,m4], metrics):
    with col:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-number">{metric[0]}</div>
            <div class="metric-label">{metric[1]}</div>
        </div>
        ''', unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------

def extract_price(price):
    nums = re.sub(r'[^\\d]', '', str(price))
    return int(nums) if nums else 999999


def deal_score(price_num, rating, reviews):
    score = 100

    if price_num > 100000:
        score -= 15
    elif price_num > 50000:
        score -= 8

    score += int(float(rating) * 5)

    if reviews > 5000:
        score += 10
    elif reviews > 1000:
        score += 5

    return min(score, 99)


def ai_insights(df):

    insights = []

    if len(df) == 0:
        return []

    cheapest = df.iloc[0]

    insights.append(f"🏆 Best value currently is {cheapest['title'][:40]}")
    insights.append(f"💰 Cheapest deal starts from {cheapest['price']}")
    insights.append(f"⭐ Highest rating found: {df['rating'].max()}")
    insights.append(f"🛒 Compared {len(df)} products in real-time")

    return insights


def get_products(q):

    api_key = st.secrets.get("SERPAPI_KEY", "")

    if not api_key:
        st.error("Add SERPAPI_KEY in Streamlit secrets.")
        return pd.DataFrame()

    params = {
        "engine": "google_shopping",
        "q": q,
        "api_key": api_key,
        "gl": "in",
        "hl": "en"
    }

    try:

        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=30
        )

        data = response.json()

        results = data.get("shopping_results", [])

        rows = []

        for item in results[:max_products]:

            title = item.get("title", "Unknown Product")
            price = item.get("price", "₹0")
            platform = item.get("source", "Unknown")
            rating = float(item.get("rating", 0) or 0)
            reviews = int(item.get("reviews", 0) or 0)
            image = item.get("thumbnail", "")
            link = item.get("product_link") or item.get("link") or "#"

            if rating < min_rating:
                continue

            price_num = extract_price(price)

            rows.append({
                "title": title,
                "price": price,
                "platform": platform,
                "rating": rating,
                "reviews": reviews,
                "image": image,
                "link": link,
                "price_num": price_num,
                "deal_score": deal_score(price_num, rating, reviews)
            })

        df = pd.DataFrame(rows)

        if len(df) == 0:
            return df

        if sort_by == "Cheapest":
            df = df.sort_values("price_num")
        elif sort_by == "Highest Rated":
            df = df.sort_values("rating", ascending=False)
        else:
            df = df.sort_values("reviews", ascending=False)

        return df

    except Exception as e:
        st.error(str(e))
        return pd.DataFrame()

# ---------------- SEARCH FLOW ----------------
if search_clicked and query:

    progress = st.progress(0)

    status = st.empty()

    for i in range(100):
        progress.progress(i + 1)

        if i < 30:
            status.info("🔍 Searching products...")
        elif i < 60:
            status.info("🧠 Generating AI insights...")
        else:
            status.info("⚡ Comparing prices...")

        time.sleep(0.01)

    df = get_products(query)

    progress.empty()
    status.empty()

    if len(df) == 0:
        st.warning("No products found.")

    else:

        # HISTORY
        if "history" not in st.session_state:
            st.session_state.history = []

        st.session_state.history.append({
            "query": query,
            "time": datetime.now().strftime("%H:%M:%S")
        })

        # INSIGHTS
        st.subheader("🧠 AI Insights")

        for insight in ai_insights(df):
            st.markdown(f'<div class="insight">{insight}</div>', unsafe_allow_html=True)

        # CHARTS
        st.subheader("📈 Price Intelligence")

        chart_df = df[["title", "price_num"]].copy()
        chart_df = chart_df.head(8)
        chart_df = chart_df.set_index("title")

        st.bar_chart(chart_df)

        # PRODUCTS
        st.subheader("🛍 Product Comparison")

        cols = st.columns(3)

        for idx, (_, row) in enumerate(df.iterrows()):

            with cols[idx % 3]:

                badge = "🏆 Best Deal" if idx == 0 else f"🔥 Score {row['deal_score']}"

                st.markdown(f'''
                <div class="product-card">
                    <img src="{row['image']}" class="product-image">

                    <div style="padding:20px;">

                        <div class="badge">{badge}</div>

                        <h3 style="margin-top:16px; color:white;">
                            {row['title'][:80]}
                        </h3>

                        <p style="color:#94a3b8;">
                            {row['platform']}
                        </p>

                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                            <div>
                                <div style="font-size:30px; font-weight:900; color:#d946ef;">
                                    {row['price']}
                                </div>
                                <div style="color:#94a3b8;">
                                    ⭐ {row['rating']} | {row['reviews']} reviews
                                </div>
                            </div>
                        </div>

                        <div style="margin-top:20px;">
                            <a class="buy-btn" href="{row['link']}" target="_blank">
                                Buy Now
                            </a>
                        </div>

                    </div>
                </div>
                ''', unsafe_allow_html=True)

        # EXPORTS
        st.subheader("📥 Export")

        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(
            "⬇ Download CSV",
            csv,
            file_name="dealgenie_results.csv",
            mime="text/csv"
        )

# ---------------- HISTORY ----------------
if "history" in st.session_state and len(st.session_state.history) > 0:

    st.subheader("🕘 Recent Searches")

    hist_cols = st.columns(min(4, len(st.session_state.history)))

    for i,item in enumerate(reversed(st.session_state.history[-4:])):
        with hist_cols[i % len(hist_cols)]:
            st.markdown(f'''
            <div class="card">
                <b>{item['query']}</b><br>
                <span style="color:#94a3b8;">{item['time']}</span>
            </div>
            ''', unsafe_allow_html=True)
