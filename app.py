import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# GLOBAL STYLE (SAFE ONLY)
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

/* CARD LOOK ONLY (NO HTML) */
.block-card {
    background: #141414;
    border-radius: 12px;
    padding: 10px;
    height: 420px;
    border: 1px solid #222;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Amazon + Netflix hybrid experience (stable UI)</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
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
        })

    return pd.DataFrame(items)

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

    df = df.sort_values("PriceNum", ascending=True)

    st.markdown("## 🔥 Top Deals")

    # =====================================================
    # NETFLIX STYLE SAFE STREAMLIT GRID
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)

        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                with st.container():

                    st.markdown('<div class="block-card">', unsafe_allow_html=True)

                    st.image(r["Image"], use_container_width=True)

                    st.markdown(f"**{str(r['Product'])[:55]}**")

                    st.write(f"💰 {r['Price']}")

                    if r.get("Rating"):
                        st.write(f"⭐ {r['Rating']} / 5")
                    else:
                        st.write("⭐ Not rated")

                    if r["Link"]:
                        st.link_button("🛒 Buy Now", r["Link"])
                    else:
                        st.button("No Link", disabled=True)

                    st.markdown('</div>', unsafe_allow_html=True)
