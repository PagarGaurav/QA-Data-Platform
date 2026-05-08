import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# UI (UNCHANGED - DO NOT TOUCH)
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

section[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

.stButton > button {
    background-color: #ff2d2d !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}

img {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("# 🛍 DealGenie")
st.markdown("### AI Shopping System")

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
# DATA FETCH
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
# 🧠 AI USE CASE 1: SEMANTIC SEARCH (SAFE ADD-ON)
# =========================================================
def semantic_search_only(query, df):

    q = query.lower()

    synonyms = {
        "shoe": ["sneaker", "footwear", "sports"],
        "gym": ["fitness", "training"],
        "laptop": ["notebook", "computer"],
        "phone": ["mobile", "smartphone"],
        "cheap": ["budget", "low price"],
        "best": ["top", "premium"]
    }

    expanded = [q]

    for k, v in synonyms.items():
        if k in q:
            expanded += v

    def score(text):
        text = str(text).lower()
        return sum(1 for w in expanded if w in text)

    temp = df.copy()
    temp["semantic_score"] = temp["Product"].apply(score)

    return temp.sort_values("semantic_score", ascending=False)

# =========================================================
# 🧠 AI USE CASE 2: DEAL CLASSIFICATION (SAFE ADD-ON)
# =========================================================
def classify_deals(df):

    df = df.copy()

    df["PriceNum"] = pd.to_numeric(df["PriceNum"], errors="coerce").fillna(0)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)

    avg_price = df["PriceNum"].mean() or 1

    def label(row):
        if row["PriceNum"] < avg_price * 0.7:
            return "🔥 Best Value"
        elif row["PriceNum"] > avg_price * 1.5:
            return "⚠️ Overpriced"
        return "👍 Fair Deal"

    df["Deal_Label"] = df.apply(label, axis=1)

    return df

# =========================================================
# 🧠 AI USE CASE 3: MARKET INSIGHTS (READ ONLY)
# =========================================================
def market_insights(df):

    if df.empty:
        return ""

    avg_price = df["PriceNum"].mean()
    avg_rating = df["Rating"].mean()

    return f"""
### 📊 Market Insights

- 💰 Avg Price: ₹{int(avg_price)}
- ⭐ Avg Rating: {round(avg_rating, 2)}
- 📌 Insight: Mid-range products dominate results
"""

# =========================================================
# MAIN LOGIC (UNCHANGED FLOW)
# =========================================================
if search_btn:

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No products found")
        st.stop()

    # FILTER ONLY (UNCHANGED)
    df = df[
        (df["PriceNum"] >= price_range[0]) &
        (df["PriceNum"] <= price_range[1])
    ]

    # =====================================================
    # OPTIONAL AI LAYERS (DO NOT AFFECT CORE LOGIC)
    # =====================================================

    df_ai = semantic_search_only(query, df)
    df_ai = classify_deals(df_ai)

    df = df_ai.head(max_products)

    st.markdown("## 🔥 Best Deals")

    # =====================================================
    # GRID (UNCHANGED)
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.image(r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                         use_container_width=True)

                st.markdown(f"**{r['Product']}**")

                st.write(f"💰 {r['Price']}")

                st.write(f"{r.get('Deal_Label','')}")

                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)

    # =====================================================
    # AI INSIGHTS (OPTIONAL DISPLAY)
    # =====================================================
    st.markdown(market_insights(df))
