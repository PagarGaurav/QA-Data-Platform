import streamlit as st
import pandas as pd
import requests
import io
import re

# =========================================================
# UI
# =========================================================
st.set_page_config(page_title="AI Product Comparison", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: white;
}

.stButton > button {
    background: linear-gradient(90deg,#6366f1,#3b82f6);
    color:white;
    border-radius:10px;
}

.stDownloadButton > button {
    background:white !important;
    color:black !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🛒 AI Product Price Comparison")

# =========================================================
# SIDEBAR
# =========================================================
api_key = st.sidebar.text_input(
    "🔑 SerpAPI Key",
    type="password"
)

country = st.sidebar.selectbox(
    "🌍 Country",
    ["India", "US"]
)

# =========================================================
# SEARCH
# =========================================================
query = st.text_input(
    "🔍 Search Product",
    placeholder="Example: black jeans"
)

# =========================================================
# FETCH PRODUCTS
# =========================================================
def fetch_products(query):

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key
    }

    if country == "India":
        params["gl"] = "in"

    response = requests.get(
        "https://serpapi.com/search",
        params=params,
        timeout=30
    )

    data = response.json()

    results = data.get("shopping_results", [])

    products = []

    for item in results:

        title = item.get("title", "")
        price = item.get("price", "")
        source = item.get("source", "")
        link = item.get("link", "")
        thumbnail = item.get("thumbnail", "")
        rating = item.get("rating", "")

        products.append({
            "Product": title,
            "Price": price,
            "Platform": source,
            "Rating": rating,
            "Link": link,
            "Image": thumbnail
        })

    return products

# =========================================================
# PRICE EXTRACTION
# =========================================================
def extract_price(p):

    nums = re.sub(r"[^\d]", "", str(p))

    return int(nums) if nums else 999999

# =========================================================
# COMPARE
# =========================================================
if st.button("Compare Prices"):

    if not api_key:
        st.warning("Enter SerpAPI key")
        st.stop()

    if not query:
        st.warning("Enter product name")
        st.stop()

    with st.spinner("Fetching real products..."):

        products = fetch_products(query)

    if not products:
        st.error("No products found")
        st.stop()

    df = pd.DataFrame(products)

    df["price_num"] = df["Price"].apply(extract_price)

    df = df.sort_values("price_num")

    # =====================================================
    # SHOW TABLE
    # =====================================================
    st.success(f"Found {len(df)} products")

    st.dataframe(
        df[[
            "Product",
            "Price",
            "Platform",
            "Rating"
        ]]
    )

    # =====================================================
    # CHEAPEST
    # =====================================================
    st.subheader("🏆 Cheapest Deals")

    cheapest = df.head(5)

    for _, row in cheapest.iterrows():

        st.markdown(f"""
        <div style="
            background:#111827;
            padding:15px;
            border-radius:12px;
            margin-bottom:10px;
        ">
            <h4>{row['Product']}</h4>
            <p>🏬 {row['Platform']}</p>
            <h3>{row['Price']}</h3>
            <p>⭐ {row['Rating']}</p>
            <a href="{row['Link']}" target="_blank">
                View Product
            </a>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # DOWNLOADS
    # =====================================================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "CSV",
            df.to_csv(index=False),
            "products.csv"
        )

    with col2:
        st.download_button(
            "JSON",
            df.to_json(orient="records"),
            "products.json"
        )

    with col3:
        buffer = io.BytesIO()

        df.to_excel(
            buffer,
            index=False
        )

        buffer.seek(0)

        st.download_button(
            "Excel",
            buffer,
            "products.xlsx"
        )
