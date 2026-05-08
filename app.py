import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# THEME
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
    url('https://images.unsplash.com/photo-1607082349566-187342175e2f');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

.row {
    display:flex;
    overflow-x:auto;
    gap:15px;
}

.row::-webkit-scrollbar {
    display:none;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 AI Shopping Assistant</h1>
<h3>Smart recommendations. Real savings. Better decisions.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# INPUTS
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("How many deals you want?", 5, 40, 5)

query = st.text_input("Search Product")

# =========================================================
# HELPERS
# =========================================================
def price_num(x):
    nums = re.sub(r"[^\d]", "", str(x))
    return int(nums) if nums else 999999

def safe_float(x):
    try:
        return float(x)
    except:
        return 0

def reviews_num(x):
    nums = re.sub(r"[^\d]", "", str(x))
    return int(nums) if nums else 0

def ai_score(row):
    return (row["rating_num"] * 50) + (row["reviews_num"] / 100) - (row["price_num"] / 1000)

# =========================================================
# FETCH DATA
# =========================================================
def fetch(q):

    params = {
        "engine": "google_shopping",
        "q": q,
        "api_key": api_key,
        "gl": "in" if country == "India" else "us",
        "hl": "en"
    }

    r = requests.get("https://serpapi.com/search", params=params)
    data = r.json()

    results = data.get("shopping_results", [])[:50]

    items = []

    for x in results:
        items.append({
            "Product": x.get("title"),
            "Price": x.get("price"),
            "Platform": x.get("source"),
            "Rating": x.get("rating", 0),
            "Reviews": x.get("reviews", 0),
            "Link": x.get("link") or x.get("product_link"),
            "Image": x.get("thumbnail") or "https://via.placeholder.com/300",
            "price_num": price_num(x.get("price")),
            "rating_num": safe_float(x.get("rating")),
            "reviews_num": reviews_num(x.get("reviews"))
        })

    return pd.DataFrame(items)

# =========================================================
# RENDER CARD ROW
# =========================================================
def row(title, items):

    if not items:
        return

    st.markdown(f"## {title}")
    cols = st.columns(4)

    for i, r in enumerate(items):

        with cols[i % 4]:
            st.image(r["Image"], use_container_width=True)
            st.markdown(f"### {r['Product'][:50]}")
            st.write(f"🏬 {r['Platform']}")
            st.write(f"💰 {r['Price']}")
            st.write(f"⭐ {r['Rating']}")
            st.link_button("🛒 Buy Now", r["Link"])

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Discover Smart Deals"):

    if not api_key or not query:
        st.warning("Enter API key and product")
        st.stop()

    df = fetch(query)

    if df.empty:
        st.warning("No products found")
        st.stop()

    df["ai_score"] = df.apply(ai_score, axis=1)

    # =====================================================
    # STRICT LIMIT POOL (NO OVERFLOW)
    # =====================================================
    pool = df.sort_values("ai_score", ascending=False).head(max_products).to_dict("records")

    # =========================
    # FEATURED
    # =========================
    featured = pool.pop(0)

    st.markdown("## 🔥 Best Deal Today")
    st.image(featured["Image"], width=300)
    st.markdown(f"### {featured['Product']}")
    st.write(f"💰 {featured['Price']}")
    st.write(f"⭐ {featured['Rating']}")
    st.link_button("🛒 Buy Now", featured["Link"])

    # =========================
    # SPLIT REMAINING STRICTLY
    # =========================
    ai_rec = pool[:2]
    pool = pool[2:]

    budget = pool[:2]
    pool = pool[2:]

    top_rated = pool[:1]
    pool = pool[1:]

    trending = pool[:1]

    # =========================
    # ROWS (NO DUPLICATES, HARD LIMIT RESPECTED)
    # =========================
    row("🧠 AI Recommended", ai_rec)
    row("💸 Budget Deals", budget)
    row("⭐ Top Rated", top_rated)
    row("🔥 Trending", trending)
