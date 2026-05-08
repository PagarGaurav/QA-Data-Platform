import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# SAFE STYLE (NO LAYOUT BREAKING)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: #0b0b0b;
    color: white;
}

/* HERO ONLY */
.hero {
    background: linear-gradient(90deg, rgba(0,0,0,0.85), rgba(0,0,0,0.4)),
    url('https://images.unsplash.com/photo-1607082350899-7e105aa886ae');
    background-size: cover;
    padding: 50px;
    border-radius: 20px;
    margin-bottom: 20px;
}

/* SIDEBAR SAFE */
section[data-testid="stSidebar"] {
    background-color: #111 !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* IMAGE FIX ONLY */
img {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO (branding fixed cleanly)
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie</h1>
<h3>AI Shopping Assistant – Find Best Deals Instantly</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Products", 4, 24, 12)
min_rating = st.sidebar.slider("Min Rating", 0.0, 5.0, 0.0)

query = st.text_input("Search Product")

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

    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)
    df = df[df["Rating"] >= min_rating]
    df = df.sort_values("PriceNum").head(max_products)

    st.markdown("## Top Deals")

    # =====================================================
    # FIXED GRID (100% STABLE STREAMLIT WAY)
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                # FIXED HEIGHT CONTAINER EFFECT
                with st.container():

                    st.image(
                        r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                        use_container_width=True
                    )

                    # TITLE FIXED SPACE
                    st.markdown(
                        f"**{str(r['Product'])[:55]}**"
                    )

                    st.write(f"💰 {r['Price']}")

                    # FIXED RATING SPACE (NO SHIFT)
                    if r["Rating"] > 0:
                        st.write(f"⭐ {r['Rating']} / 5")
                    else:
                        st.write("⭐ —")

                    # BUTTON SAFE
                    if r["Link"]:
                        st.link_button("Buy Now 🛒", r["Link"])
                    else:
                        st.button("No Link", disabled=True)
