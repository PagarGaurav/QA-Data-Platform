import streamlit as st
import pandas as pd
import requests
import io
import re

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI Product Price Comparison",
    layout="wide"
)

# =========================================================
# UI
# =========================================================
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
    border:none;
    padding:10px 16px;
    font-weight:600;
}

.stDownloadButton > button {
    background:white !important;
    color:black !important;
    border-radius:10px;
    font-weight:600;
}

section[data-testid="stSidebar"] {
    background-color:#0b0f19 !important;
}

.card {
    background:#111827;
    padding:20px;
    border-radius:16px;
    margin-bottom:18px;
    border:1px solid #1f2937;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
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
    ["India", "US"],
    index=0
)

max_products = st.sidebar.slider(
    "📦 Max Products",
    5,
    50,
    20
)

# =========================================================
# SEARCH INPUT
# =========================================================
query = st.text_input(
    "🔍 Search Product",
    placeholder="Example: black jeans, nike shoes, iphone 15"
)

# =========================================================
# HELPERS
# =========================================================
def extract_price(price):

    nums = re.sub(r"[^\d]", "", str(price))

    return int(nums) if nums else 999999


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

    # =====================================================
    # API ERROR HANDLING
    # =====================================================
    if response.status_code != 200:
        raise Exception("SerpAPI request failed")

    data = response.json()

    # =====================================================
    # SERPAPI ERROR
    # =====================================================
    if "error" in data:
        raise Exception(data["error"])

    shopping_results = data.get("shopping_results", [])

    # =====================================================
    # LIMIT PRODUCTS
    # =====================================================
    shopping_results = shopping_results[:max_products]

    products = []

    for item in shopping_results:

        title = item.get("title", "")
        price = item.get("price", "")
        source = item.get("source", "")

        # =================================================
        # BEST AVAILABLE LINK
        # =================================================
        link = item.get("product_link")

        if not link:
            link = item.get("link")

        if not link:
            continue

        thumbnail = item.get("thumbnail", "")
        rating = item.get("rating", "")
        reviews = item.get("reviews", "")

        products.append({
            "Product": title,
            "Price": price,
            "Platform": source,
            "Rating": rating,
            "Reviews": reviews,
            "Link": link,
            "Image": thumbnail
        })

    return products


# =========================================================
# SEARCH BUTTON
# =========================================================
if st.button("Compare Prices"):

    if not api_key:
        st.warning("Please enter SerpAPI key")
        st.stop()

    if not query:
        st.warning("Please enter product name")
        st.stop()

    # =====================================================
    # FETCH PRODUCTS
    # =====================================================
    with st.spinner("Fetching real products..."):

        try:
            products = fetch_products(query)

        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    # =====================================================
    # NO PRODUCTS
    # =====================================================
    if not products:
        st.error("No products found")
        st.stop()

    # =====================================================
    # DATAFRAME
    # =====================================================
    df = pd.DataFrame(products)

    # =====================================================
    # CLEAN PRICE
    # =====================================================
    df["price_num"] = df["Price"].apply(extract_price)

    # =====================================================
    # SORT BY CHEAPEST
    # =====================================================
    df = df.sort_values("price_num")

    # =====================================================
    # SUMMARY
    # =====================================================
    st.success(f"Found {len(df)} products")

    cheapest_price = df.iloc[0]["Price"]
    cheapest_platform = df.iloc[0]["Platform"]

    c1, c2 = st.columns(2)

    with c1:
        st.metric("🏆 Cheapest Price", cheapest_price)

    with c2:
        st.metric("🛍 Cheapest Platform", cheapest_platform)

    st.markdown("---")

    # =====================================================
    # PRODUCT CARDS
    # =====================================================
    st.subheader("🛒 Product Comparison")

    min_price = df["price_num"].min()

    for _, row in df.iterrows():

        st.markdown("""
        <div class="card">
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 3])

        # =================================================
        # IMAGE
        # =================================================
        with col1:

            if row["Image"]:
                st.image(
                    row["Image"],
                    width=180
                )

        # =================================================
        # DETAILS
        # =================================================
        with col2:

            # CLICKABLE TITLE
            st.markdown(
                f"""
                <a href="{row['Link']}"
                   target="_blank"
                   rel="noopener noreferrer"
                   style="text-decoration:none;color:white;">
                    <h3>{row['Product']}</h3>
                </a>
                """,
                unsafe_allow_html=True
            )

            st.write(f"🏬 Platform: {row['Platform']}")

            st.write(f"💰 Price: {row['Price']}")

            if row["Rating"]:
                st.write(f"⭐ Rating: {row['Rating']}")

            if row["Reviews"]:
                st.write(f"📝 Reviews: {row['Reviews']}")

            # =================================================
            # CHEAPEST BADGE
            # =================================================
            if row["price_num"] == min_price:
                st.success("🏆 Cheapest Deal")

            # =================================================
            # BUY BUTTON
            # =================================================
            st.markdown(
                f"""
                <a href="{row['Link']}"
                   target="_blank"
                   rel="noopener noreferrer">
                    <button style="
                        background: linear-gradient(90deg,#6366f1,#3b82f6);
                        color:white;
                        border:none;
                        padding:10px 18px;
                        border-radius:10px;
                        cursor:pointer;
                        font-weight:600;
                    ">
                        🛒 Buy Now
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================
    # TABLE VIEW
    # =====================================================
    st.markdown("---")

    st.subheader("📊 Table View")

    st.dataframe(
        df[[
            "Product",
            "Price",
            "Platform",
            "Rating",
            "Reviews"
        ]],
        use_container_width=True
    )

    # =====================================================
    # DOWNLOADS
    # =====================================================
    st.markdown("---")

    st.subheader("⬇ Download Results")

    d1, d2, d3 = st.columns(3)

    # CSV
    with d1:

        st.download_button(
            "CSV",
            df.to_csv(index=False),
            "products.csv"
        )

    # JSON
    with d2:

        st.download_button(
            "JSON",
            df.to_json(orient="records"),
            "products.json"
        )

    # EXCEL
    with d3:

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
