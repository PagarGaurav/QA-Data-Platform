import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# DARK AI SHOPPING THEME
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

/* CARD */
.card {
    background:#111;
    border-radius:14px;
    overflow:hidden;
    border:1px solid #222;
    transition:0.3s;
}

.card:hover {
    transform:scale(1.03);
    border:1px solid #ff2d2d;
}

/* ROW */
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
<h1>🛍 AI Shopping Assistant</h1>
<h3>Smart recommendations. Real savings. Better decisions.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# INPUTS
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("How many deals you want?", 5, 40, 10)

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
# WHY BUY INSIGHT ENGINE
# =========================================================
def why_buy(row):
    reasons = []

    if row["rating_num"] >= 4:
        reasons.append("Highly rated by buyers")
    if row["reviews_num"] > 500:
        reasons.append("Trusted by many users")
    if row["price_num"] < 2000:
        reasons.append("Budget-friendly price")
    if "amazon" in str(row["Platform"]).lower():
        reasons.append("Reliable marketplace")

    if not reasons:
        reasons.append("Balanced choice across price and rating")

    return " • " + " | ".join(reasons)

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

    results = data.get("shopping_results", [])[:max_products]

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
# ROW RENDER
# =========================================================
def row(title, df):

    st.markdown(f"## {title}")

    cols = st.columns(4)

    for i, (_, r) in enumerate(df.iterrows()):

        with cols[i % 4]:

            st.image(r["Image"], use_container_width=True)

            st.markdown(f"### {r['Product'][:50]}")
            st.write(f"🏬 {r['Platform']}")
            st.write(f"💰 {r['Price']}")
            st.write(f"⭐ {r['Rating']}")

            st.caption(why_buy(r))   # 👈 NEW INSIGHT

            st.link_button("🛒 Buy Now", r["Link"])

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Discover Smart Deals"):

    if not api_key or not query:
        st.warning("Enter API key and product")
        st.stop()

    df = fetch(query)

    df["ai_score"] = df.apply(ai_score, axis=1)

    # APPLY FILTER STRICTLY
    df = df.head(max_products)

    # =========================
    # FEATURED DEAL
    # =========================
    featured = df.iloc[0]

    st.markdown("## 🔥 Best Deal Today")

    st.image(featured["Image"], width=300)

    st.markdown(f"### {featured['Product']}")
    st.write(f"💰 {featured['Price']}")
    st.write(f"⭐ {featured['Rating']}")

    st.caption("💡 Why this deal: " + why_buy(featured))

    st.link_button("🛒 Buy Now", featured["Link"])

    # =========================
    # AI RECOMMENDED
    # =========================
    row("🧠 AI Recommended Picks",
        df.sort_values("ai_score", ascending=False).head(8))

    # =========================
    # OTHER ROWS
    # =========================
    row("💸 Budget Friendly Deals",
        df.sort_values("price_num").head(8))

    row("⭐ Top Rated Products",
        df.sort_values("rating_num", ascending=False).head(8))

    row("🔥 Most Popular",
        df.sort_values("reviews_num", ascending=False).head(8))
