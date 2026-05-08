import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import urlparse
from openai import OpenAI

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top,#0b0b0b,#000);
    color:white;
    font-family: Arial;
}

/* HERO */
.hero {
    background:
    linear-gradient(90deg, rgba(0,0,0,0.88), rgba(0,0,0,0.45)),
    url('https://images.unsplash.com/photo-1483985988355-763728e1935b');
    background-size:cover;
    background-position:center;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

/* PRODUCT CARD */
.card {
    background:#111;
    border-radius:14px;
    padding:12px;
    border:1px solid #222;
    height:590px;
}

/* IMAGES */
img {
    border-radius:10px;
}

/* SEARCH BUTTON */
.stButton > button {
    background:#ff2d2d !important;
    color:white !important;
    font-weight:800 !important;
    border:none !important;
    border-radius:10px !important;
}

/* BUY BUTTON */
.stLinkButton a {
    background:#ff2d2d !important;
    color:white !important;
    border-radius:8px !important;
    padding:8px 12px !important;
    text-decoration:none !important;
    font-weight:700 !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"]{
    background:#000 !important;
}

section[data-testid="stSidebar"] *{
    color:white !important;
}

section[data-testid="stSidebar"] input{
    background-color:#000 !important;
    color:white !important;
    border:1px solid #333 !important;
}

section[data-testid="stSidebar"] button{
    background-color:#000 !important;
    border:none !important;
}

section[data-testid="stSidebar"] button svg{
    stroke:white !important;
    fill:white !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div{
    background:#000 !important;
    color:white !important;
}

section[data-testid="stSidebar"] .stSlider{
    color:white !important;
}

/* AI BADGES */
.badge {
    background:#1c1c1c;
    border:1px solid #333;
    padding:6px 10px;
    border-radius:8px;
    margin-top:8px;
    font-size:13px;
    font-weight:700;
    color:#00ff95;
}

.portal {
    color:#ffcc00;
    font-size:13px;
    margin-top:4px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart deals. Real savings. Best prices online.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## ☰ Menu")

api_key = st.sidebar.text_input(
    "SerpAPI Key",
    type="password"
)

openai_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password"
)

country = st.sidebar.selectbox(
    "Country",
    ["India", "US"]
)

max_products = st.sidebar.slider(
    "Show Results",
    1,
    10,
    10
)

price_range = st.sidebar.slider(
    "Price Range",
    500,
    500000,
    (500, 500000)
)

# =========================================================
# SEARCH
# =========================================================
query = st.text_input("🔎 Search Product")

# =========================================================
# OPENAI CLIENT
# =========================================================
client = OpenAI(api_key=openai_key) if openai_key else None

# =========================================================
# GET PORTAL NAME
# =========================================================
def get_store_name(link):

    if not link:
        return "Unknown"

    domain = urlparse(link).netloc.lower()

    if "amazon" in domain:
        return "Amazon"

    elif "flipkart" in domain:
        return "Flipkart"

    elif "myntra" in domain:
        return "Myntra"

    elif "ajio" in domain:
        return "Ajio"

    elif "meesho" in domain:
        return "Meesho"

    return domain.replace("www.", "")

# =========================================================
# FETCH PRODUCTS
# =========================================================
def fetch(q, api_key, country):

    params = {
        "engine": "google_shopping",
        "q": q,
        "api_key": api_key,
        "gl": "in" if country == "India" else "us",
        "hl": "en"
    }

    response = requests.get(
        "https://serpapi.com/search",
        params=params
    )

    data = response.json()

    results = data.get("shopping_results", [])

    items = []

    for x in results:

        price_text = x.get("price") or "0"

        price_num = int(
            re.sub(r"[^\d]", "", str(price_text)) or 0
        )

        rating = x.get("rating")

        try:
            rating_num = float(rating)
        except:
            rating_num = 0

        link = x.get("product_link") or x.get("link") or ""

        items.append({
            "Product": x.get("title"),
            "Price": price_text,
            "PriceNum": price_num,
            "Link": link,
            "Store": get_store_name(link),
            "Image": x.get("thumbnail"),
            "Rating": rating if rating else "N/A",
            "RatingNum": rating_num
        })

    return pd.DataFrame(items)

# =========================================================
# AI SHOPPING COPILOT
# =========================================================
def ask_dealgenie(question, context=""):

    if client is None:
        return "⚠️ Enter OpenAI API key."

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role":"system",
                    "content":"""
You are DealGenie AI Shopping Assistant.

Your role:
- Recommend BEST product
- Find CHEAPEST option
- Tell WHERE TO BUY
- Explain WHY shortly

Keep answers concise and useful.
"""
                },
                {
                    "role":"user",
                    "content":f"""
Question:
{question}

Products:
{context}

Return:
1. Best Product
2. Cheapest Deal
3. Where To Buy
4. Reason
"""
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# =========================================================
# SEARCH BUTTON
# =========================================================
if st.button("🔎 Search Product"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No products found")
        st.stop()

    # FILTER
    df = df[
        (df["PriceNum"] >= price_range[0]) &
        (df["PriceNum"] <= price_range[1])
    ]

    # LIMIT
    df = df.head(max_products)

    # =====================================================
    # AI BEST PRODUCT LOGIC
    # =====================================================
    best_value_index = (
        (df["RatingNum"] * 1000) - df["PriceNum"]
    ).idxmax()

    cheapest_index = df["PriceNum"].idxmin()

    # SAVE SESSION
    st.session_state["products_df"] = df

    # CLEAR OLD AI OUTPUT
    st.session_state["last_answer"] = ""

    st.markdown("## 🔥 Best Deals")

    df = df.reset_index(drop=True)

    # =====================================================
    # PRODUCT GRID
    # =====================================================
    for i in range(0, len(df), 3):

        cols = st.columns(3)

        row = df.iloc[i:i+3]

        for col, (idx, r) in zip(cols, row.iterrows()):

            with col:

                st.markdown(
                    '<div class="card">',
                    unsafe_allow_html=True
                )

                img = (
                    r["Image"]
                    if r["Image"]
                    else "https://via.placeholder.com/300"
                )

                st.image(
                    img,
                    use_container_width=True
                )

                st.markdown(
                    f"**{str(r['Product'])[:60]}**"
                )

                st.write(f"💰 {r['Price']}")

                st.write(f"⭐ {r['Rating']}")

                # STORE NAME
                st.markdown(
                    f"<div class='portal'>🛒 Store: {r['Store']}</div>",
                    unsafe_allow_html=True
                )

                # CHEAPEST TAG
                if idx == cheapest_index:
                    st.markdown(
                        "<div class='badge'>💰 Cheapest Deal</div>",
                        unsafe_allow_html=True
                    )

                # BEST VALUE TAG
                if idx == best_value_index:
                    st.markdown(
                        "<div class='badge'>🏆 Best Rated Value</div>",
                        unsafe_allow_html=True
                    )

                if r["Link"]:

                    st.link_button(
                        "🛒 Buy Now",
                        r["Link"]
                    )

                else:

                    st.button(
                        "No Link Available",
                        disabled=True
                    )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

# =========================================================
# ASK DEALGENIE
# =========================================================
st.sidebar.markdown("---")
st.sidebar.markdown("## 💬 Ask DealGenie")

user_q = st.sidebar.text_input(
    "Ask anything",
    key="chat_input"
)

# =========================================================
# AI ASK BUTTON
# =========================================================
if st.sidebar.button("Ask Assistant"):

    df_context = st.session_state.get(
        "products_df",
        pd.DataFrame()
    )

    context = ""

    if not df_context.empty:

        context = df_context[
            ["Product", "Price", "Rating", "Store"]
        ].to_string(index=False)

    answer = ask_dealgenie(
        user_q,
        context
    )

    st.session_state["last_answer"] = answer

# =========================================================
# AI OUTPUT
# =========================================================
if st.session_state.get("last_answer"):

    st.sidebar.markdown("### 🧠 AI Insight")

    st.sidebar.write(
        st.session_state["last_answer"]
    )
