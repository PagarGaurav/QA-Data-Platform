import streamlit as st
import pandas as pd
import requests
import re
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
    background: linear-gradient(90deg, rgba(0,0,0,0.85), rgba(0,0,0,0.4)),
    url('https://images.unsplash.com/photo-1607082350899-7e105aa886ae');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

/* CARD STYLE */
.card {
    background:#111;
    border-radius:14px;
    padding:12px;
    border:1px solid #222;
    height:520px;
}

/* IMAGE FIX */
img {
    border-radius:10px;
}

/* BUY BUTTON */
.stLinkButton a {
    background-color:#ff2d2d !important;
    color:white !important;
    padding:8px 12px;
    border-radius:8px;
    font-weight:700;
    text-decoration:none;
}

/* SEARCH BUTTON */
.stButton > button {
    background:#ff2d2d !important;
    color:white !important;
    font-weight:800;
    border-radius:10px;
    border:none;
}

/* =======================================================
SIDEBAR FIX
======================================================= */

section[data-testid="stSidebar"] {
    background:#000 !important;
}

/* FIX ALL SIDEBAR TEXT */
section[data-testid="stSidebar"] * {
    color:white !important;
}

/* FIX INPUT TEXT */
section[data-testid="stSidebar"] input {
    background:#111 !important;
    color:white !important;
}

/* FIX SELECTBOX */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background:#111 !important;
    color:white !important;
}

/* FIX DROPDOWN TEXT */
section[data-testid="stSidebar"] span {
    color:white !important;
}

/* FIX PASSWORD EYE ICON */
section[data-testid="stSidebar"] svg {
    fill:white !important;
}

/* FIX SLIDER */
section[data-testid="stSidebar"] .stSlider {
    color:white !important;
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
    5,
    5
)

price_range = st.sidebar.slider(
    "Price Range",
    500,
    10000,
    (500, 10000)
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

    r = requests.get(
        "https://serpapi.com/search",
        params=params
    )

    data = r.json()

    results = data.get("shopping_results", [])

    items = []

    for x in results:

        price_text = x.get("price") or "0"

        price_num = int(
            re.sub(r"[^\d]", "", str(price_text)) or 0
        )

        items.append({
            "Product": x.get("title"),
            "Price": price_text,
            "PriceNum": price_num,
            "Link": x.get("product_link") or x.get("link") or "",
            "Image": x.get("thumbnail"),
            "Rating": x.get("rating") or "N/A"
        })

    return pd.DataFrame(items)

# =========================================================
# AI COPILOT
# =========================================================
def ask_dealgenie(question, context=""):

    if client is None:
        return "⚠️ Enter OpenAI API key."

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are DealGenie AI Shopping Assistant.

Your job:
- Pick BEST product
- Pick CHEAPEST product
- Tell WHERE TO BUY
- Explain WHY briefly

Keep answers short and useful.
"""
                },
                {
                    "role": "user",
                    "content": f"""
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

    df = df[
        (df["PriceNum"] >= price_range[0]) &
        (df["PriceNum"] <= price_range[1])
    ]

    df = df.head(max_products)

    st.session_state["products_df"] = df

    st.markdown("## 🔥 Best Deals")

    df = df.reset_index(drop=True)

    # =====================================================
    # PRODUCT GRID
    # =====================================================
    for i in range(0, len(df), 3):

        row = df.iloc[i:i+3]
        cols = st.columns(3)

        for col, (_, r) in zip(cols, row.iterrows()):

            with col:

                st.markdown(
                    '<div class="card">',
                    unsafe_allow_html=True
                )

                img = r["Image"] if r["Image"] else "https://via.placeholder.com/300"

                st.image(
                    img,
                    use_container_width=True
                )

                st.markdown(
                    f"**{str(r['Product'])[:60]}**"
                )

                st.write(f"💰 {r['Price']}")
                st.write(f"⭐ {r['Rating']}")

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
# AI BUTTON
# =========================================================
if st.sidebar.button("Ask Assistant"):

    df_context = st.session_state.get(
        "products_df",
        pd.DataFrame()
    )

    context = ""

    if not df_context.empty:

        context = df_context[
            ["Product", "Price", "Rating", "Link"]
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
