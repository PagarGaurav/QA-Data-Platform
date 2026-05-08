import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# BLACK THEME (UNCHANGED)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: #0b0b0b;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #111 !important;
}

/* SIDEBAR FIX */
section[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white !important;
}

section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

/* BUTTON */
.stButton > button {
    background-color: #ff2d2d !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
}

.stButton > button:hover {
    background-color: #ff0000 !important;
}

/* CARD STABILITY */
.card {
    height: 440px;
    background: #141414;
    border-radius: 12px;
    padding: 10px;
    border: 1px solid #222;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card img {
    height: 220px;
    width: 100%;
    object-fit: cover;
    border-radius: 10px;
}

.title {
    height: 40px;
    overflow: hidden;
    font-size: 13px;
    font-weight: 600;
}

.price {
    min-height: 18px;
    color: #00ffae;
    font-weight: 700;
}

.rating {
    height: 18px;
    font-size: 12px;
    color: #aaa;
}

.buy {
    display: block;
    margin-top: 10px;
    background: #ff2d2d;
    color: white;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-weight: 700;
    text-decoration: none;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
# 🛍 DealGenie
### AI Shopping Intelligence System
""")

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 1, 5, 5)
price_range = st.sidebar.slider("Price Range (₹)", 500, 10000, (500, 10000))

query = st.text_input("Search Product")

search_btn = st.button("Search")

# =========================================================
# FETCH DATA
# =========================================================
def fetch(q, api_key, country):

    params = {
        "engine": "google_shopping",
        "q": q,
        "api_key": api_key,
        "gl": "in" if country == "India" else "us",
        "hl": "en"
    }

    r = requests.get("https://serpapi.com/search", params=params)
    data = r.json()

    results = data.get("shopping_results", [])

    items = []

    for x in results:
        price_text = x.get("price") or "0"
        price_num = int(re.sub(r"[^\d]", "", str(price_text)) or 0)

        items.append({
            "Product": x.get("title"),
            "Price": price_text,
            "PriceNum": price_num,
            "Link": x.get("product_link") or x.get("link") or "",
            "Image": x.get("thumbnail"),
            "Rating": x.get("rating"),
        })

    return pd.DataFrame(items)

# =========================================================
# AI ENGINE (PRODUCTION CORE)
# =========================================================
def ai_engine(df):

    if df.empty:
        return df

    df = df.copy()

    df["PriceNum"] = pd.to_numeric(df["PriceNum"], errors="coerce").fillna(0)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)

    max_price = df["PriceNum"].max() or 1

    df["price_score"] = 1 - (df["PriceNum"] / max_price)
    df["rating_score"] = df["Rating"] / 5

    df["AI_Score"] = (df["price_score"] * 0.55 + df["rating_score"] * 0.45) * 100

    def label(x):
        if x >= 80:
            return "🔥 Best Deal"
        elif x >= 60:
            return "👍 Good Deal"
        elif x >= 40:
            return "⚖️ Average"
        else:
            return "⚠️ Overpriced"

    df["AI_Label"] = df["AI_Score"].apply(label)

    def explain(row):
        reasons = []
        if row["price_score"] > 0.7:
            reasons.append("Low price advantage")
        if row["rating_score"] > 0.8:
            reasons.append("High rating")
        if row["PriceNum"] < df["PriceNum"].median():
            reasons.append("Below market price")
        return ", ".join(reasons) if reasons else "Standard product"

    df["AI_Explain"] = df.apply(explain, axis=1)

    return df.sort_values("AI_Score", ascending=False)

# =========================================================
# AI INSIGHTS
# =========================================================
def ai_insights(df):

    if df.empty:
        return ""

    avg_price = df["PriceNum"].mean()
    avg_rating = df["Rating"].mean()

    best = df.iloc[0] if len(df) > 0 else None

    return f"""
### 🤖 AI Insights

- 💰 Avg Price: ₹{int(avg_price)}
- ⭐ Avg Rating: {round(avg_rating, 2)}

### 🔥 Top Recommendation
- {best['Product'] if best is not None else 'N/A'}
- Score: {round(best['AI_Score'], 2) if best is not None else 'N/A'}

### 📊 Market Insight
- Value-based ranking performs better than price-only filtering
"""

# =========================================================
# MAIN
# =========================================================
if search_btn:

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No results found")
        st.stop()

    # PRICE FILTER
    df = df[
        (df["PriceNum"] >= price_range[0]) &
        (df["PriceNum"] <= price_range[1])
    ]

    # AI PROCESSING
    df = ai_engine(df).head(max_products)

    st.markdown("## 🔥 Top AI Deals")

    # GRID
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.image(
                    r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                    use_container_width=True
                )

                st.markdown(f"**{r['Product']}**")

                st.write(f"💰 {r['Price']}")

                st.write(f"{r['AI_Label']}")

                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)

    # AI INSIGHTS
    st.markdown(ai_insights(df))
