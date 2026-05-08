import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# ORIGINAL BRAND UI (RESTORED)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top,#0b0b0b,#000);
    color:white;
    font-family: Arial;
}

/* BUTTON */
.stButton > button {
    background:#ff2d2d;
    color:white;
    font-weight:800;
    border-radius:10px;
}

/* HERO */
.hero {
    background: linear-gradient(90deg,#000,rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1518770660439-4636190af475');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

/* CARD STYLE RESTORED */
.card {
    background:#111;
    border-radius:14px;
    padding:12px;
    border:1px solid #222;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO (UNCHANGED BRAND)
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart recommendations. Real savings.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR FILTER
# =========================================================
st.sidebar.markdown("## 🎛 Controls")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Show Results", 5, 40, 5)

query = st.text_input("🔎 Search Product")

# =========================================================
# FETCH
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

        # ✅ FIX: multiple link fallbacks
        link = x.get("link") or x.get("product_link") or ""

        items.append({
            "Product": x.get("title"),
            "Price": price_text,
            "PriceNum": price_num,
            "Link": link,
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
# SCORE
# =========================================================
def score(row):
    return 1 / (row["PriceNum"] + 1)

# =========================================================
# SAFE BUY (FIXED)
# =========================================================
def safe_buy(url, key):

    if not url or str(url).strip() == "":
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
    # BEST DEAL (CARD STYLE RESTORED)
    # =====================================================
    best = df.iloc[0]

    st.markdown("## 🔥 Best Deal")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.image(best["Image"], width=300)
    st.markdown(f"### {best['Product']}")
    st.write(best["Price"])
    safe_buy(best["Link"], 0)
    st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # MORE DEALS
    # =====================================================
    st.markdown("## 🛍 More Deals")

    cols = st.columns(3)

    for i, r in df.iterrows():

        with cols[i % 3]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.image(r["Image"], use_container_width=True)
            st.write(r["Product"])
            st.write(r["Price"])
            safe_buy(r["Link"], i + 1)
            st.markdown('</div>', unsafe_allow_html=True)
