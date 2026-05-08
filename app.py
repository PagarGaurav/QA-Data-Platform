import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG (KEEP DEFAULT THEME - NO COLOR BREAKING)
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# HERO (UNCHANGED VISUAL)
# =========================================================
st.markdown("""
# 🛍 DealGenie
### AI Shopping Assistant
""")

# =========================================================
# SIDEBAR (FIX VISIBILITY ONLY - MINIMAL CSS)
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
    # SAFE HORIZONTAL FEEL (STREAMLIT WAY)
    # =====================================================

    cols = st.columns(5)  # fixed stable grid instead of CSS scroll

    for i, (_, r) in enumerate(df.iterrows()):

        col = cols[i % 5]

        with col:

            st.image(r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                     use_container_width=True)

            st.markdown(f"**{str(r['Product'])[:55]}**")

            st.write(f"💰 {r['Price']}")

            if r.get("Rating"):
                st.write(f"⭐ {r['Rating']} / 5")
            else:
                st.write("")

            if r["Link"]:
                st.link_button("🛒 Buy Now", r["Link"])
            else:
                st.button("No Link", disabled=True)
