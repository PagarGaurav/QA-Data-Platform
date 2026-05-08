import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# STYLE (NETFLIX STYLE FIXED UI)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: #0b0b0b;
    color: white;
    font-family: Arial;
}

/* HERO */
.hero {
    background: linear-gradient(90deg, rgba(0,0,0,0.9), rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1607082350899-7e105aa886ae');
    background-size: cover;
    padding: 60px;
    border-radius: 20px;
    margin-bottom: 20px;
}

/* SCROLL ROW */
.row {
    display: flex;
    overflow-x: auto;
    gap: 16px;
    padding: 10px 5px;
}

/* HIDE SCROLLBAR */
.row::-webkit-scrollbar {
    display: none;
}

/* CARD */
.card {
    min-width: 240px;
    max-width: 240px;
    background: #141414;
    border-radius: 12px;
    overflow: hidden;
    flex-shrink: 0;
    border: 1px solid #222;
}

/* IMAGE */
.card img {
    width: 100%;
    height: 220px;
    object-fit: cover;
}

/* CONTENT */
.card-body {
    padding: 10px;
}

/* TITLE */
.title {
    font-size: 13px;
    font-weight: 600;
    height: 38px;
    overflow: hidden;
}

/* PRICE */
.price {
    color: #00ffae;
    font-weight: 700;
    margin-top: 5px;
}

/* BUY BUTTON */
.buy {
    display: block;
    margin-top: 10px;
    background: #ff2d2d;
    color: white;
    text-align: center;
    padding: 6px;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 700;
}

.buy:hover {
    background: #ff0000;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart deals. Real savings. Netflix style product discovery.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## ☰ Menu")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 10, 30, 10)

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
            "Link": x.get("product_link") or x.get("link") or "",
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

    st.markdown("## 🔥 Top Deals")

    # =====================================================
    # NETFLIX STYLE ROW
    # =====================================================
    html = '<div class="row">'

    for _, r in df.iterrows():

        img = r["Image"] if r["Image"] else "https://via.placeholder.com/300"

        html += f"""
        <div class="card">
            <img src="{img}">
            <div class="card-body">
                <div class="title">{str(r['Product'])[:60]}</div>
                <div class="price">{r['Price']}</div>
                <div style="font-size:12px; color:#aaa;">
                    ⭐ {r['Rating'] if r.get('Rating') else '-'} / 5
                </div>

                <a class="buy" href="{r['Link']}" target="_blank">
                    🛒 Buy Now
                </a>
            </div>
        </div>
        """

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)
