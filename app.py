import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# STYLE (CLEAN + FIXED)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top,#0b0b0b,#000);
    color:white;
    font-family: Arial;
}

/* HERO */
.hero {
    background: linear-gradient(90deg, rgba(0,0,0,0.85), rgba(0,0,0,0.4)),
    url('https://images.unsplash.com/photo-1607082350899-7e105aa886ae');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

/* PRODUCT CARD (FIXED EQUAL HEIGHT) */
.product-card {
    background:#111;
    border-radius:14px;
    padding:12px;
    border:1px solid #222;
    height:520px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
}

/* IMAGE */
.img-box {
    width:100%;
    height:220px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#1a1a1a;
    border-radius:10px;
    overflow:hidden;
}

.img-box img {
    max-height:100%;
    max-width:100%;
    object-fit:contain;
}

/* BUY BUTTON */
.stLinkButton a {
    background-color:#ff2d2d !important;
    color:white !important;
    padding:8px 12px;
    border-radius:8px;
    font-weight:700;
    text-decoration:none;
    display:inline-block;
}

/* SEARCH BUTTON */
.stButton > button {
    background:#ff2d2d;
    color:white;
    font-weight:800;
    border-radius:10px;
}

/* RATING */
.rating {
    color:#ffd700;
    font-weight:700;
}

.small {
    font-size:12px;
    color:#bbb;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart deals. Real savings. Best prices online.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## ☰ Menu")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Show Results", 6, 30, 6)

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
            "Link": x.get("link") or x.get("product_link") or "",
            "Image": x.get("thumbnail"),
            "Rating": x.get("rating"),
            "Reviews": x.get("reviews")
        })

    return pd.DataFrame(items)

# =========================================================
# FILTER
# =========================================================
def is_relevant(title, q):
    return q.lower().split()[0] in str(title).lower()

def score(row):
    return 1 / (row["PriceNum"] + 1)

# =========================================================
# BUY BUTTON
# =========================================================
def safe_buy(url, key):
    if url:
        st.link_button("🛒 Buy Now", url, key=f"buy_{key}")
    else:
        st.button("No Link Available", disabled=True, key=f"no_{key}")

# =========================================================
# MAIN
# =========================================================
if st.button("🔎 Search Product"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No products found")
        st.stop()

    df = df[df["Product"].apply(lambda x: is_relevant(x, query))]
    df["Score"] = df.apply(score, axis=1)
    df = df.sort_values("Score", ascending=False).head(max_products)

    st.markdown("## 🔥 Best Deals")

    cols = st.columns(3)

    for i, r in df.iterrows():

        with cols[i % 3]:

            st.markdown('<div class="product-card">', unsafe_allow_html=True)

            img = r["Image"] if r["Image"] else "https://via.placeholder.com/300"

            st.markdown(f"""
            <div class="img-box">
                <img src="{img}">
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"**{str(r['Product'])[:60]}**")

            st.write(f"💰 {r['Price']}")

            # Rating
            rating = r.get("Rating")
            reviews = r.get("Reviews")

            if rating:
                st.markdown(f"<div class='rating'>⭐ {rating} / 5</div>", unsafe_allow_html=True)

            if reviews:
                st.markdown(f"<div class='small'>{reviews} reviews</div>", unsafe_allow_html=True)

            safe_buy(r["Link"], i)

            st.markdown('</div>', unsafe_allow_html=True)
