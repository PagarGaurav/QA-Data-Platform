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
# CUSTOM UI
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
    background: linear-gradient(145deg,#111827,#1e293b);
    padding:22px;
    border-radius:20px;
    margin-bottom:22px;
    border:1px solid #334155;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-3px);
    border:1px solid #6366f1;
}

.metric-card {
    background: linear-gradient(145deg,#111827,#1e293b);
    padding:18px;
    border-radius:18px;
    text-align:center;
    border:1px solid #334155;
    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
}

.ai-box {
    background: linear-gradient(145deg,#1e293b,#0f172a);
    padding:18px;
    border-radius:16px;
    border-left:5px solid #8b5cf6;
    margin-bottom:18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.2);
}

.stTextInput input {
    background:#111827 !important;
    color:white !important;
    border-radius:14px !important;
    border:1px solid #334155 !important;
    padding:14px !important;
    font-size:16px !important;
}

.stSelectbox div[data-baseweb="select"] {
    background:#111827 !important;
    border-radius:12px !important;
}

.stSlider {
    padding-top:10px;
}

hr {
    border-color:#1e293b !imp
</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.markdown("""
<div style='text-align:center;padding:10px 0 25px 0;'>
    <h1 style='font-size:52px;font-weight:800;margin-bottom:5px;'>🛍 DealGenie</h1>
    <h3 style='color:#94a3b8;font-weight:400;'>AI Shopping Assistant</h3>
    <p style='color:#64748b;font-size:18px;'>Compare real-time prices across top shopping platforms with AI-powered insights</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("⚙ Settings")

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
    15
)

sort_option = st.sidebar.selectbox(
    "📊 Sort By",
    [
        "Cheapest First",
        "Highest Rated",
        "Most Reviewed"
    ]
)

# =========================================================
# SEARCH
# =========================================================
query = st.text_input(
    "🔍 Search Product",
    placeholder="Example: black jeans, iphone 15, nike shoes"
)

# =========================================================
# HELPERS
# =========================================================
def extract_price(price):

    nums = re.sub(r"[^\d]", "", str(price))

    return int(nums) if nums else 999999


def extract_reviews(value):

    nums = re.sub(r"[^\d]", "", str(value))

    return int(nums) if nums else 0


def safe_rating(value):

    try:
        return float(value)
    except:
        return 0


# =========================================================
# AI INSIGHT ENGINE
# =========================================================
def generate_ai_insights(df):

    insights = []

    if len(df) == 0:
        return insights

    cheapest = df.iloc[0]

    insights.append(
        f"🏆 Cheapest product available on {cheapest['Platform']} for {cheapest['Price']}"
    )

    best_rated = df.sort_values("rating_num", ascending=False).iloc[0]

    insights.append(
        f"⭐ Highest rated product: {best_rated['Product'][:60]}"
    )

    most_reviewed = df.sort_values("reviews_num", ascending=False).iloc[0]

    insights.append(
        f"🔥 Most reviewed product has {most_reviewed['Reviews']} reviews"
    )

    if df["price_num"].max() > 0:

        savings = (
            df["price_num"].max() -
            df["price_num"].min()
        )

        insights.append(
            f"💰 Potential savings opportunity: ₹{savings:,}"
        )

    return insights


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

    if response.status_code != 200:
        raise Exception("SerpAPI request failed")

    data = response.json()

    if "error" in data:
        raise Exception(data["error"])

    shopping_results = data.get("shopping_results", [])

    shopping_results = shopping_results[:max_products]

    products = []

    for item in shopping_results:

        title = item.get("title", "")
        price = item.get("price", "")
        source = item.get("source", "")

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
            "Image": thumbnail,
            "price_num": extract_price(price),
            "rating_num": safe_rating(rating),
            "reviews_num": extract_reviews(reviews)
        })

    return products


# =========================================================
# MAIN BUTTON
# =========================================================
if st.button("🚀 Compare Prices"):

    if not api_key:
        st.warning("Please enter SerpAPI key")
        st.stop()

    if not query:
        st.warning("Please enter product name")
        st.stop()

    with st.spinner("Fetching real-time products and generating AI insights..."):

        try:
            products = fetch_products(query)

        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    if not products:
        st.error("No products found")
        st.stop()

    # =====================================================
    # DATAFRAME
    # =====================================================
    df = pd.DataFrame(products)

    # =====================================================
    # SORTING
    # =====================================================
    if sort_option == "Cheapest First":
        df = df.sort_values("price_num")

    elif sort_option == "Highest Rated":
        df = df.sort_values("rating_num", ascending=False)

    elif sort_option == "Most Reviewed":
        df = df.sort_values("reviews_num", ascending=False)

    # =====================================================
    # METRICS
    # =====================================================
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "🛒 Products",
            len(df)
        )

    with c2:
        st.metric(
            "🏆 Cheapest",
            df.iloc[0]["Price"]
        )

    with c3:
        st.metric(
            "⭐ Top Rating",
            str(df["rating_num"].max())
        )

    with c4:
        st.metric(
            "🕒 Updated",
            datetime.now().strftime("%H:%M:%S")
        )

    # =====================================================
    # AI INSIGHTS
    # =====================================================
    st.markdown("---")
    st.subheader("🧠 AI Shopping Insights")

    insights = generate_ai_insights(df)

    for insight in insights:

        st.markdown(
            f'''
            <div class="ai-box">
                {insight}
            </div>
            ''',
            unsafe_allow_html=True
        )

    # =====================================================
    # PRODUCT CARDS
    # =====================================================
    st.markdown("---")
    st.subheader("🛍 Product Comparison")

    min_price = df["price_num"].min()

    for _, row in df.iterrows():

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 3])

        # IMAGE
        with col1:

            if row["Image"]:
                st.image(
                    row["Image"],
                    width=180
                )

        # DETAILS
        with col2:

            st.markdown(
                f'''
                <a href="{row['Link']}"
                   target="_blank"
                   rel="noopener noreferrer"
                   style="text-decoration:none;color:white;">
                    <h3>{row['Product']}</h3>
                </a>
                ''',
                unsafe_allow_html=True
            )

            st.write(f"🏬 Platform: {row['Platform']}")
            st.write(f"💰 Price: {row['Price']}")

            if row["Rating"]:
                st.write(f"⭐ Rating: {row['Rating']}")

            if row["Reviews"]:
                st.write(f"📝 Reviews: {row['Reviews']}")

            # CHEAPEST BADGE
            if row["price_num"] == min_price:
                st.success("🏆 Best Deal Available")

            # BUY BUTTON
            st.markdown(
                f'''
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
                ''',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    # =====================================================
    # TABLE VIEW
    # =====================================================
    st.markdown("---")
    st.subheader("📊 Comparison Table")

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
    st.subheader("⬇ Export Results")

    d1, d2, d3 = st.columns(3)

    with d1:

        st.download_button(
            "CSV",
            df.to_csv(index=False),
            "products.csv"
        )

    with d2:

        st.download_button(
            "JSON",
            df.to_json(orient="records"),
            "products.json"
        )

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

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    "Enterprise AI Shopping Assistant • Real-time product comparison • AI-ready architecture"
)
