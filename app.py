import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG (UNCHANGED UI)
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# YOUR ORIGINAL HERO (UNCHANGED)
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie</h1>
<h3>AI Shopping Assistant</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ONLY FIX: CARD STABILITY CSS (NO COLOR / UI CHANGE)
# =========================================================
st.markdown("""
<style>

/* ONLY STRUCTURE FIX - NO DESIGN CHANGE */

/* FORCE EQUAL CARD HEIGHT */
.card {
    height: 440px !important;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

/* FIX IMAGE HEIGHT */
.card img {
    height: 220px !important;
    width: 100%;
    object-fit: cover;
}

/* TITLE FIX (PREVENT EXPANSION) */
.title {
    height: 40px;
    overflow: hidden;
}

/* RATING FIX (RESERVED SPACE) */
.rating {
    height: 18px;
}

/* PRICE FIX */
.price {
    min-height: 18px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR (UNCHANGED)
# =========================================================
st.sidebar.markdown("## Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
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
            "Rating": x.get("rating"),
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

    df = df.sort_values("PriceNum").head(20)

    st.markdown("## 🔥 Top Deals")

    # =====================================================
    # YOUR ORIGINAL GRID (UNCHANGED STRUCTURE)
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.markdown('<div class="card">', unsafe_allow_html=True)

                # IMAGE
                st.image(
                    r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                    use_container_width=True
                )

                # TITLE (FIXED SPACE ONLY)
                st.markdown(
                    f"<div class='title'>{r['Product']}</div>",
                    unsafe_allow_html=True
                )

                # PRICE
                st.markdown(
                    f"<div class='price'>💰 {r['Price']}</div>",
                    unsafe_allow_html=True
                )

                # RATING (FIXED SPACE ONLY)
                rating = r["Rating"] if r.get("Rating") else ""

                st.markdown(
                    f"<div class='rating'>{'⭐ ' + str(rating) + ' / 5' if rating else '&nbsp;'}</div>",
                    unsafe_allow_html=True
                )

                # BUY BUTTON (UNCHANGED LOGIC)
                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)

                st.markdown('</div>', unsafe_allow_html=True)
