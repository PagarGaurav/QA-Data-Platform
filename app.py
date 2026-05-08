import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# GLOBAL SAFE STYLE FIX
# =========================================================
st.markdown("""
<style>

/* MAIN BACKGROUND */
.stApp {
    background: #0b0b0b;
    color: white;
}

/* HERO */
.hero {
    background: linear-gradient(90deg, rgba(0,0,0,0.85), rgba(0,0,0,0.4)),
    url('https://images.unsplash.com/photo-1607082350899-7e105aa886ae');
    background-size: cover;
    padding: 50px;
    border-radius: 20px;
    margin-bottom: 20px;
}

/* SIDEBAR FIX */
section[data-testid="stSidebar"] {
    background-color: #111 !important;
}

/* Sidebar text visible */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p {
    color: white !important;
    opacity: 1 !important;
}

/* Sidebar input text */
section[data-testid="stSidebar"] input {
    color: black !important;
}

/* SEARCH BUTTON FIX */
.stButton > button {
    background-color: #ff2d2d !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 10px 16px !important;
}

.stButton > button:hover {
    background-color: #ff0000 !important;
}

/* CARD STYLE */
.card {
    background: #141414;
    border-radius: 12px;
    padding: 10px;
    height: 430px;
    border: 1px solid #222;
}

/* IMAGE FIX */
.card img {
    height: 220px;
    width: 100%;
    object-fit: cover;
    border-radius: 10px;
}

/* TITLE FIX */
.title {
    font-size: 13px;
    font-weight: 600;
    height: 42px;
    overflow: hidden;
}

/* RATING FIX */
.rating {
    height: 18px;
    font-size: 12px;
    color: #aaa;
}

/* BUY BUTTON (RED FIXED) */
.buy-btn {
    display: block;
    margin-top: 10px;
    background: #ff2d2d;
    color: white;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-weight: 700;
    text-decoration: none;
}

.buy-btn:hover {
    background: #ff0000;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie</h1>
<h3>AI Shopping Assistant — Find Best Deals Instantly</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Products", 4, 24, 12)
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
            "Rating": x.get("rating")
        })

    return pd.DataFrame(items)

# =========================================================
# MAIN
# =========================================================
if st.button("Search"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No results found")
        st.stop()

    df = df.sort_values("PriceNum").head(max_products)

    st.markdown("## 🔥 Top Deals")

    # =====================================================
    # STABLE GRID
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.image(
                    r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                    use_container_width=True
                )

                st.markdown(f"<div class='title'>{str(r['Product'])[:55]}</div>",
                            unsafe_allow_html=True)

                st.write(f"💰 {r['Price']}")

                rating = r["Rating"] if r.get("Rating") else ""
                st.markdown(
                    f"<div class='rating'>{'⭐ ' + str(rating) + ' / 5' if rating else '&nbsp;'}</div>",
                    unsafe_allow_html=True
                )

                # RED BUY BUTTON (FIXED)
                if r["Link"]:
                    st.markdown(f"""
                    <a class="buy-btn" href="{r['Link']}" target="_blank">
                        🛒 Buy Now
                    </a>
                    """, unsafe_allow_html=True)
                else:
                    st.button("No Link", disabled=True)

                st.markdown('</div>', unsafe_allow_html=True)
