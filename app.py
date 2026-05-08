import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Netflix Shop", layout="wide")

# =========================================================
# NETFLIX RED + BLACK UI
# =========================================================
st.markdown("""
<style>

.stApp {
    background:#000;
    color:white;
}

/* BUTTON */
.stButton > button {
    background:#e50914;
    color:white;
    font-weight:800;
    border-radius:10px;
}

/* HERO */
.hero {
    background: linear-gradient(90deg,#000,rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1523275335684-37898b6baf30');
    background-size:cover;
    padding:50px;
    border-radius:20px;
    margin-bottom:20px;
}

.card {
    background:#141414;
    border-radius:12px;
    overflow:hidden;
    border:1px solid #222;
    transition:0.3s;
}

.card:hover {
    transform:scale(1.04);
    border:1px solid #e50914;
}

.row {
    display:flex;
    overflow-x:auto;
    gap:15px;
}

.row::-webkit-scrollbar {
    display:none;
}

.item {
    min-width:220px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI</h1>
<h3>Netflix Style Smart Shopping</h3>
<p>AI recommends. You save money.</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 5, 40, 15)

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
    # 🔥 SIMPLE AI RANKING MODEL
    return (
        (row["rating_num"] * 40) +
        (row["reviews_num"] / 100) -
        (row["price_num"] / 1000)
    )

# =========================================================
# FETCH
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

    results = data.get("shopping_results", [])[:max_products]

    items = []

    for x in results:

        link = x.get("product_link") or x.get("link") or "#"
        img = x.get("thumbnail") or "https://via.placeholder.com/300"

        items.append({
            "Product": x.get("title"),
            "Price": x.get("price"),
            "Platform": x.get("source"),
            "Rating": x.get("rating", 0),
            "Reviews": x.get("reviews", 0),
            "Link": link,
            "Image": img,
            "price_num": price_num(x.get("price")),
            "rating_num": safe_float(x.get("rating")),
            "reviews_num": reviews_num(x.get("reviews"))
        })

    return pd.DataFrame(items)

# =========================================================
# ROW RENDER
# =========================================================
def row(title, df):

    st.markdown(f"## {title}")
    st.markdown("<div class='row'>", unsafe_allow_html=True)

    for _, r in df.iterrows():

        st.markdown(f"""
        <div class="item">
        <a href="{r['Link']}" target="_blank">

        <div class="card">

            <img src="{r['Image']}" width="100%">

            <div style="padding:10px;">

                <div style="color:#e50914;font-size:12px;">
                    {r['Platform']}
                </div>

                <div style="font-weight:700;height:40px;overflow:hidden;">
                    {r['Product'][:50]}
                </div>

                <div>💰 {r['Price']}</div>
                <div>⭐ {r['Rating']}</div>

            </div>

        </div>

        </a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Start AI Shopping"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query)

    # =========================
    # AI SCORE
    # =========================
    df["ai_score"] = df.apply(ai_score, axis=1)

    featured = df.iloc[0]

    # =========================
    # FEATURED
    # =========================
    st.markdown("## 🔥 Featured Deal")

    st.markdown(f"""
    <div style="background:#111;padding:20px;border-radius:15px;border:1px solid #e50914;">
        <h2>{featured['Product']}</h2>
        <h3 style="color:#e50914;">💰 {featured['Price']}</h3>
        <a href="{featured['Link']}" target="_blank">
            <button>🛒 Buy Now</button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # AI ROW (NEW)
    # =========================
    row("🧠 AI Recommended For You", df.sort_values("ai_score", ascending=False).head(10))

    # =========================
    # NETFLIX ROWS
    # =========================
    row("💸 Budget Picks", df.sort_values("price_num").head(10))
    row("⭐ Top Rated", df.sort_values("rating_num", ascending=False).head(10))
    row("🔥 Trending", df.sort_values("reviews_num", ascending=False).head(10))

    # =========================
    # TABLE
    # =========================
    st.markdown("---")
    st.dataframe(df)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("DealGenie AI • Fixed Netflix Shopping Engine")
