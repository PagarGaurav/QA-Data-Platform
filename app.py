import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="DealGenie - AI Shopping Assistant",
    layout="wide"
)

# =========================================================
# YOUR EXISTING CSS (UNCHANGED)
# =========================================================
st.markdown("""<style>
.stApp {
    background: linear-gradient(135deg,#070b14,#0f172a,#111827);
    color: #f8fafc;
}
</style>""", unsafe_allow_html=True)

# =========================================================
# HEADER (UNCHANGED)
# =========================================================
st.markdown("""
<div style='text-align:center;'>
<h1>🛍 DealGenie</h1>
<h3>AI Shopping Assistant</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("Menu")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 5, 50, 15)

sort_option = st.sidebar.selectbox(
    "Sort By",
    ["Cheapest First", "Highest Rated", "Most Reviewed"]
)

query = st.text_input("Search Product")

# =========================================================
# HELPERS
# =========================================================
def extract_price(price):
    nums = re.sub(r"[^\d]", "", str(price))
    return int(nums) if nums else 999999

def safe_rating(value):
    try:
        return float(value)
    except:
        return 0

def extract_reviews(value):
    nums = re.sub(r"[^\d]", "", str(value))
    return int(nums) if nums else 0

# =========================================================
# PRODUCT KEY (NEW FEATURE CORE)
# =========================================================
def product_key(title):
    title = title.lower()
    words = re.sub(r"[^a-z0-9 ]", "", title).split()
    return " ".join(words[:5])   # first 5 words cluster

# =========================================================
# FETCH PRODUCTS
# =========================================================
def fetch_products(search_query):

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "api_key": api_key,
        "gl": "in" if country == "India" else "us",
        "hl": "en"
    }

    response = requests.get(
        "https://serpapi.com/search",
        params=params,
        timeout=30
    )

    data = response.json()

    results = data.get("shopping_results", [])[:max_products]

    products = []

    for item in results:

        title = item.get("title", "")
        price = item.get("price", "")
        source = item.get("source", "")

        products.append({
            "Product": title,
            "Price": price,
            "Platform": source,
            "Rating": item.get("rating", ""),
            "Reviews": item.get("reviews", ""),
            "Link": item.get("link"),
            "price_num": extract_price(price),
            "rating_num": safe_rating(item.get("rating", "")),
            "reviews_num": extract_reviews(item.get("reviews", "")),
            "key": product_key(title)   # 🔥 NEW
        })

    return products

# =========================================================
# MAIN
# =========================================================
if st.button("Compare Prices"):

    if not api_key or not query:
        st.warning("Enter API key and product")
        st.stop()

    products = fetch_products(query)

    df = pd.DataFrame(products)

    # SORT
    if sort_option == "Cheapest First":
        df = df.sort_values("price_num")
    elif sort_option == "Highest Rated":
        df = df.sort_values("rating_num", ascending=False)
    elif sort_option == "Most Reviewed":
        df = df.sort_values("reviews_num", ascending=False)

    # =====================================================
    # METRICS
    # =====================================================
    st.subheader("Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("Products", len(df))
    c2.metric("Cheapest", df.iloc[0]["Price"])
    c3.metric("Max Rating", df["rating_num"].max())

    # =====================================================
    # 🆕 LIVE COMPARISON FEATURE
    # =====================================================
    st.markdown("---")
    st.subheader("🔍 Live Product Comparison (Cross Platform)")

    grouped = df.groupby("key")

    for key, group in grouped:

        if len(group) < 2:
            continue  # only show comparisons

        st.markdown(f"### 🛍 {group.iloc[0]['Product'][:60]}")

        cols = st.columns(len(group))

        for i, (_, row) in enumerate(group.iterrows()):

            with cols[i]:

                st.markdown(f"""
                <div style="
                    background:#111827;
                    padding:15px;
                    border-radius:15px;
                    border:1px solid #334155;
                ">
                <b>{row['Platform']}</b><br><br>

                💰 {row['Price']}<br>
                ⭐ {row['Rating']}<br>
                📝 {row['Reviews']}<br><br>

                <a href="{row['Link']}" target="_blank">
                    🔗 View
                </a>

                </div>
                """, unsafe_allow_html=True)

    # =====================================================
    # TABLE VIEW (existing)
    # =====================================================
    st.markdown("---")
    st.subheader("Table View")

    st.dataframe(df[[
        "Product",
        "Price",
        "Platform",
        "Rating",
        "Reviews"
    ]])

    # =====================================================
    # DOWNLOAD
    # =====================================================
    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        "products.csv"
    )

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("DealGenie AI • Enhanced Product Intelligence")
