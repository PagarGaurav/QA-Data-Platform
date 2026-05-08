import streamlit as st
import pandas as pd
import requests
import re
import io
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="DealGenie - Netflix Shopping AI",
    layout="wide"
)

# =========================================================
# 🎬 NETFLIX STYLE THEME (RED + BLACK)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: #000000;
    color: white;
    font-family: Arial;
}

/* BUTTON */
.stButton > button {
    background: #e50914;
    color: white;
    font-weight: 800;
    border-radius: 10px;
    padding: 12px 18px;
    border: none;
}

.stButton > button:hover {
    background: #ff0a16;
    transform: scale(1.02);
}

/* HERO */
.hero {
    background: linear-gradient(90deg,#000 35%,rgba(0,0,0,0.2)),
                url('https://images.unsplash.com/photo-1523275335684-37898b6baf30');
    background-size: cover;
    padding: 60px 40px;
    border-radius: 20px;
    margin-bottom: 20px;
}

/* ROW SCROLL */
.row {
    display: flex;
    overflow-x: auto;
    gap: 15px;
    padding: 10px 0;
}

.row::-webkit-scrollbar {
    display: none;
}

/* CARD */
.card {
    background: #141414;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #222;
    transition: 0.3s;
    min-width: 220px;
    max-width: 220px;
}

.card:hover {
    transform: scale(1.05);
    border: 1px solid #e50914;
}

.card img {
    width: 100%;
    height: 240px;
    object-fit: cover;
}

/* TEXT */
.badge {
    color: #e50914;
    font-size: 12px;
    font-weight: 700;
}

.price {
    color: white;
    font-weight: 800;
    margin-top: 5px;
}

.rating {
    color: gold;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO SECTION
# =========================================================
st.markdown("""
<div class="hero">
<h1 style="font-size:50px;">🛍 DealGenie</h1>
<h3>Netflix Style AI Shopping Experience</h3>
<p style="color:#ccc;">
Search once. Compare everywhere. Shop like streaming content.
</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("⚙ Controls")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 5, 50, 15)

query = st.text_input("🔍 Search Product")

# =========================================================
# HELPERS
# =========================================================
def extract_price(price):
    nums = re.sub(r"[^\d]", "", str(price))
    return int(nums) if nums else 999999

def safe_rating(v):
    try:
        return float(v)
    except:
        return 0

def extract_reviews(v):
    nums = re.sub(r"[^\d]", "", str(v))
    return int(nums) if nums else 0

def product_key(title):
    words = re.sub(r"[^a-zA-Z0-9 ]", "", title.lower()).split()
    return " ".join(words[:5])

# =========================================================
# FETCH PRODUCTS
# =========================================================
def fetch_products(q):

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
            "Rating": x.get("rating"),
            "Reviews": x.get("reviews"),
            "Link": x.get("link"),
            "Image": x.get("thumbnail"),
            "price_num": extract_price(x.get("price")),
            "rating_num": safe_rating(x.get("rating")),
            "reviews_num": extract_reviews(x.get("reviews")),
            "key": product_key(x.get("title",""))
        })

    return items

# =========================================================
# RENDER ROW (NETFLIX STYLE)
# =========================================================
def render_row(title, df):

    st.markdown(f"## {title}")
    st.markdown("<div class='row'>", unsafe_allow_html=True)

    for _, r in df.iterrows():

        st.markdown(f"""
        <a href="{r['Link']}" target="_blank" style="text-decoration:none;color:white;">
        <div class="card">

            <img src="{r['Image']}">

            <div style="padding:10px;">

                <div class="badge">{r['Platform']}</div>

                <div style="font-weight:700;height:40px;overflow:hidden;">
                    {r['Product'][:55]}
                </div>

                <div class="price">💰 {r['Price']}</div>

                <div class="rating">⭐ {r['Rating']}</div>

            </div>

        </div>
        </a>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# MAIN APP
# =========================================================
if st.button("🚀 Start Netflix Shopping Experience"):

    if not api_key:
        st.warning("Enter API key")
        st.stop()

    if not query:
        st.warning("Enter product")
        st.stop()

    products = fetch_products(query)
    df = pd.DataFrame(products)

    # =========================
    # FEATURED PRODUCT
    # =========================
    featured = df.iloc[0]

    st.markdown("## 🔥 Featured Deal")

    st.markdown(f"""
    <div style="
        background:#111;
        padding:25px;
        border-radius:15px;
        border:1px solid #e50914;
        margin-bottom:20px;
    ">

        <h2>{featured['Product']}</h2>
        <h3 style="color:#e50914;">💰 {featured['Price']}</h3>
        <p>⭐ {featured['Rating']} | 📝 {featured['Reviews']}</p>

        <a href="{featured['Link']}" target="_blank">
            <button>🛒 Buy Now</button>
        </a>

    </div>
    """, unsafe_allow_html=True)

    # =========================
    # ROWS (NETFLIX STYLE)
    # =========================
    render_row(
        "💸 Budget Picks",
        df.sort_values("price_num").head(10)
    )

    render_row(
        "⭐ Top Rated",
        df.sort_values("rating_num", ascending=False).head(10)
    )

    render_row(
        "🔥 Trending Now",
        df.sort_values("reviews_num", ascending=False).head(10)
    )

    # =========================
    # DOWNLOAD
    # =========================
    st.markdown("---")

    st.download_button(
        "⬇ Download CSV",
        df.to_csv(index=False),
        "dealgenie.csv"
    )

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("DealGenie • Netflix Style AI Shopping Experience")
