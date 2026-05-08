import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# THEME (UNCHANGED)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top,#0b0b0b,#000);
    color:white;
    font-family: Arial;
}

.stButton > button {
    background:#ff2d2d;
    color:white;
    font-weight:800;
    border-radius:10px;
}

.hero {
    background: linear-gradient(90deg,#000,rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1518770660439-4636190af475');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart recommendations. Real savings.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = None

# =========================================================
# SIDEBAR (ONLY COUNT FILTER)
# =========================================================
st.sidebar.markdown("## 🎛 Controls")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Show Results", 5, 40, 5)

query = st.text_input("🔎 Search Product")

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

    results = data.get("shopping_results", [])  # NO slicing here

    items = []

    for x in results:
        price_text = x.get("price") or "0"
        price_num = int(re.sub(r"[^\d]", "", str(price_text)) or 0)

        items.append({
            "Product": x.get("title"),
            "Price": price_text,
            "PriceNum": price_num,
            "Link": x.get("link"),
            "Image": x.get("thumbnail")
        })

    return pd.DataFrame(items)

# =========================================================
# INTENT DETECTION
# =========================================================
def detect_intent(q):

    q = q.lower()

    if any(x in q for x in ["tshirt", "t-shirt", "tee"]):
        return "tshirt"
    if any(x in q for x in ["shoe", "sneaker", "running"]):
        return "shoes"
    if "mobile" in q:
        return "mobile"
    if "laptop" in q:
        return "laptop"

    return "generic"

# =========================================================
# RELEVANCE FILTER
# =========================================================
def is_relevant(title, intent):

    t = str(title).lower()

    mapping = {
        "tshirt": ["tshirt", "t-shirt", "tee", "shirt", "polo"],
        "shoes": ["shoe", "sneaker", "running"],
        "mobile": ["mobile", "phone"],
        "laptop": ["laptop"]
    }

    keys = mapping.get(intent, [])

    if not keys:
        return True

    return any(k in t for k in keys)

# =========================================================
# SIMPLE SCORING (AI RANKING)
# =========================================================
def score(row):

    return 1 / (row["PriceNum"] + 1)

# =========================================================
# SAFE BUY BUTTON
# =========================================================
def safe_buy(url):

    if not url:
        st.button("🛒 No Link Available", disabled=True)
    else:
        st.link_button("🛒 Buy Now", url)

# =========================================================
# LIMIT FUNCTION (IMPORTANT FIX)
# =========================================================
def apply_limit(df, limit):

    if df is None or df.empty:
        return df

    return df.head(limit)

# =========================================================
# MAIN FLOW (CORRECT ORDER FIXED)
# =========================================================
if st.button("🚀 Search Product"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    # 1. FETCH
    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No products found")
        st.stop()

    # 2. FILTER BY INTENT
    intent = detect_intent(query)
    df = df[df["Product"].apply(lambda x: is_relevant(x, intent))]

    if df.empty:
        st.warning("No relevant products found")
        st.stop()

    # 3. AI RANKING
    df["Score"] = df.apply(score, axis=1)
    df = df.sort_values("Score", ascending=False)

    # 4. APPLY LIMIT (THIS FIXES YOUR ISSUE)
    df = apply_limit(df, max_products)

    st.session_state.df = df

    # =====================================================
    # DISPLAY RESULTS
    # =====================================================
    st.markdown("## 🔥 Best Deal")

    best = df.iloc[0]

    st.image(best["Image"], width=300)
    st.markdown(f"### {best['Product']}")
    st.write(best["Price"])

    safe_buy(best["Link"])

    st.markdown("## 🛍 More Deals")

    cols = st.columns(3)

    for i, r in df.iterrows():

        with cols[i % 3]:
            st.image(r["Image"], use_container_width=True)
            st.write(r["Product"])
            st.write(r["Price"])
            safe_buy(r["Link"])
