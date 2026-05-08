import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# BLACK THEME (PRESERVED)
# =========================================================
st.markdown("""
<style>

/* MAIN BACKGROUND */
.stApp {
    background: #0b0b0b;
    color: white;
}

/* SIDEBAR BACKGROUND */
section[data-testid="stSidebar"] {
    background-color: #111 !important;
}

/* =========================================================
   FIX: SIDEBAR VISIBILITY ISSUE (NEW ADDITION ONLY)
   ========================================================= */

/* Labels (API Key, Country etc.) */
section[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600 !important;
}

/* Sidebar headers/text */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p {
    color: white !important;
}

/* Input text */
section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

/* Selectbox text */
section[data-testid="stSidebar"] div {
    color: white !important;
}

/* =========================================================
   SEARCH BUTTON FIX
   ========================================================= */
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

/* IMAGE */
img {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
# 🛍 DealGenie
### AI Shopping Assistant
""")

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 1, 5, 5)
price_range = st.sidebar.slider("Price Range (₹)", 500, 10000, (500, 10000))

query = st.text_input("Search Product")

search_btn = st.button("Search")

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
if search_btn:

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No results found")
        st.stop()

    df["PriceNum"] = pd.to_numeric(df["PriceNum"], errors="coerce").fillna(0)

    # PRICE FILTER
    df = df[
        (df["PriceNum"] >= price_range[0]) &
        (df["PriceNum"] <= price_range[1])
    ]

    df = df.head(max_products)

    st.markdown("## 🔥 Top Deals")

    # =====================================================
    # STABLE GRID (UNCHANGED LOGIC)
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.image(
                    r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                    use_container_width=True
                )

                st.markdown(f"**{r['Product']}**")

                st.write(f"💰 {r['Price']}")

                rating = r["Rating"] if r.get("Rating") else ""
                st.write(f"{'⭐ ' + str(rating) + ' / 5' if rating else ''}")

                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)
