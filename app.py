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
# SIDEBAR
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

    results = data.get("shopping_results", [])

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
# INTENT
# =========================================================
def detect_intent(q):

    q = q.lower()

    if "tshirt" in q or "tee" in q:
        return "tshirt"
    if "shoe" in q or "sneaker" in q:
        return "shoes"
    if "mobile" in q:
        return "mobile"
    if "laptop" in q:
        return "laptop"

    return "generic"

# =========================================================
# FILTER
# =========================================================
def is_relevant(title, intent):

    t = str(title).lower()

    mapping = {
        "tshirt": ["tshirt", "t-shirt", "tee", "shirt"],
        "shoes": ["shoe", "sneaker", "running"],
        "mobile": ["mobile", "phone"],
        "laptop": ["laptop"]
    }

    keys = mapping.get(intent, [])

    if not keys:
        return True

    return any(k in t for k in keys)

# =========================================================
# AI SCORE
# =========================================================
def score(row):
    return 1 / (row["PriceNum"] + 1)

# =========================================================
# SAFE BUY BUTTON (FIXED DUPLICATE ERROR)
# =========================================================
def safe_buy(url, key):

    if not url:
        st.button("🛒 No Link Available", disabled=True, key=f"no_{key}")
    else:
        st.link_button("🛒 Buy Now", url, key=f"buy_{key}")

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Search Product"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No products found")
        st.stop()

    intent = detect_intent(query)

    df = df[df["Product"].apply(lambda x: is_relevant(x, intent))]

    if df.empty:
        st.warning("No relevant products found")
        st.stop()

    df["Score"] = df.apply(score, axis=1)
    df = df.sort_values("Score", ascending=False)

    df = df.head(max_products)

    # =====================================================
    # BEST DEAL
    # =====================================================
    best = df.iloc[0]

    st.markdown("## 🔥 Best Deal")

    st.image(best["Image"], width=300)
    st.markdown(f"### {best['Product']}")
    st.write(best["Price"])

    safe_buy(best["Link"], 0)

    # =====================================================
    # MORE DEALS
    # =====================================================
    st.markdown("## 🛍 More Deals")

    cols = st.columns(3)

    for i, r in enumerate(df.iterrows()):

        idx, row = r

        with cols[i % 3]:
            st.image(row["Image"], use_container_width=True)
            st.write(row["Product"])
            st.write(row["Price"])

            safe_buy(row["Link"], i + 1)
