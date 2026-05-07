import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import io

# =========================================================
# UI (SIMILAR STYLE)
# =========================================================
st.set_page_config(page_title="AI Price Comparison", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: #e5e7eb;
}

.stButton > button {
    background: linear-gradient(90deg, #6366f1, #3b82f6);
    color: white;
    border-radius: 10px;
}

.stDownloadButton > button {
    background-color: white !important;
    color: black !important;
    font-weight: 600;
    border-radius: 8px;
}

label {
    color: white !important;
}

section[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
}

.card {
    background:#111827;
    padding:15px;
    border-radius:12px;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛒 AI Product Price Comparison")

# =========================================================
# SIDEBAR
# =========================================================
platforms = st.sidebar.multiselect(
    "🛍 Select Platforms",
    [
        "Pantaloons",
        "Lifestyle",
        "Myntra",
        "Ajio"
    ],
    default=["Pantaloons", "Lifestyle"]
)

# =========================================================
# HELPERS
# =========================================================
headers = {
    "User-Agent": "Mozilla/5.0"
}

# =========================================================
# PANTALOONS SCRAPER
# =========================================================
def scrape_pantaloons(query):

    products = []

    try:

        url = f"https://www.pantaloons.com/search?q={query}"

        r = requests.get(url, headers=headers, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ")

        prices = re.findall(r"₹\s?[\d,]+", text)

        for i, p in enumerate(prices[:10]):

            products.append({
                "Platform": "Pantaloons",
                "Product": f"{query.title()} Item {i+1}",
                "Price": p
            })

    except:
        pass

    return products

# =========================================================
# LIFESTYLE SCRAPER
# =========================================================
def scrape_lifestyle(query):

    products = []

    try:

        url = f"https://www.lifestylestores.com/in/en/search?q={query}"

        r = requests.get(url, headers=headers, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ")

        prices = re.findall(r"₹\s?[\d,]+", text)

        for i, p in enumerate(prices[:10]):

            products.append({
                "Platform": "Lifestyle",
                "Product": f"{query.title()} Item {i+1}",
                "Price": p
            })

    except:
        pass

    return products

# =========================================================
# MYNTRA SCRAPER
# =========================================================
def scrape_myntra(query):

    products = []

    try:

        url = f"https://www.myntra.com/{query}"

        r = requests.get(url, headers=headers, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ")

        prices = re.findall(r"Rs\.?\s?[\d,]+", text)

        for i, p in enumerate(prices[:10]):

            products.append({
                "Platform": "Myntra",
                "Product": f"{query.title()} Item {i+1}",
                "Price": p
            })

    except:
        pass

    return products

# =========================================================
# AJIO SCRAPER
# =========================================================
def scrape_ajio(query):

    products = []

    try:

        url = f"https://www.ajio.com/search/?text={query}"

        r = requests.get(url, headers=headers, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ")

        prices = re.findall(r"₹\s?[\d,]+", text)

        for i, p in enumerate(prices[:10]):

            products.append({
                "Platform": "Ajio",
                "Product": f"{query.title()} Item {i+1}",
                "Price": p
            })

    except:
        pass

    return products

# =========================================================
# SEARCH
# =========================================================
query = st.text_input(
    "🔍 Search Product",
    placeholder="Example: black jeans"
)

if st.button("Compare Prices"):

    if not query:
        st.warning("Enter product name")
        st.stop()

    all_products = []

    with st.spinner("Searching products..."):

        if "Pantaloons" in platforms:
            all_products.extend(scrape_pantaloons(query))

        if "Lifestyle" in platforms:
            all_products.extend(scrape_lifestyle(query))

        if "Myntra" in platforms:
            all_products.extend(scrape_myntra(query))

        if "Ajio" in platforms:
            all_products.extend(scrape_ajio(query))

    # =====================================================
    # FALLBACK
    # =====================================================
    if not all_products:

        all_products = [
            {
                "Platform": "Demo",
                "Product": f"{query.title()} Slim Fit",
                "Price": "₹1999"
            },
            {
                "Platform": "Demo",
                "Product": f"{query.title()} Regular Fit",
                "Price": "₹2499"
            }
        ]

    # =====================================================
    # DATAFRAME
    # =====================================================
    df = pd.DataFrame(all_products)

    st.success(f"Found {len(df)} products")

    st.dataframe(df)

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

    # =====================================================
    # CHEAPEST
    # =====================================================
    st.subheader("🏆 Cheapest Products")

    def extract_price(p):

        nums = re.sub(r"[^\d]", "", str(p))

        return int(nums) if nums else 999999

    df["price_num"] = df["Price"].apply(extract_price)

    cheapest = df.sort_values("price_num").head(5)

    for _, row in cheapest.iterrows():

        st.markdown(f"""
        <div class="card">
            <h4>{row['Product']}</h4>
            <p>🏬 {row['Platform']}</p>
            <h3>{row['Price']}</h3>
        </div>
        """, unsafe_allow_html=True)
