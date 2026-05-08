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
# UI FIX (SIDEBAR VISIBILITY + SCROLL)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: #0b0b0b;
    color: white;
}

/* SIDEBAR FIX */
section[data-testid="stSidebar"] {
    background-color: #111 !important;
    overflow-y: auto !important;
    max-height: 100vh !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* INPUT FIX */
section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

/* BUTTON FIX */
.stButton > button {
    background-color: #ff2d2d !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}

img {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("# 🛍 DealGenie")
st.markdown("### 🧠 DealGenie AI Shopping Assistant")

# =========================================================
# SIDEBAR INPUTS
# =========================================================
st.sidebar.markdown("## Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")

country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 1, 5, 5)
price_range = st.sidebar.slider("Price Range (₹)", 500, 10000, (500, 10000))

query = st.text_input("Search Product")
search_btn = st.button("Search")

# =========================================================
# OPENAI CLIENT (SAFE)
# =========================================================
client = OpenAI(api_key=openai_key) if openai_key else None

# =========================================================
# SESSION STATE FIX
# =========================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

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
# GPT COPILOT
# =========================================================
def ask_dealgenie(question, context=""):

    if client is None:
        return "⚠️ Enter OpenAI API key in sidebar."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are DealGenie AI Shopping Assistant. Help users choose and compare products."
                },
                {
                    "role": "user",
                    "content": f"{question}\n\nContext:\n{context}"
                }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# =========================================================
# MAIN PRODUCT FLOW
# =========================================================
df = pd.DataFrame()

if search_btn:

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

    st.markdown("## 🔥 AI Recommended Products")

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
                st.write(f"⭐ {r['Rating']}")

                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)

# =========================================================
# 💬 SIDEBAR COPILOT (FULLY FIXED)
# =========================================================
st.sidebar.markdown("---")
st.sidebar.markdown("## 💬 Ask DealGenie")

user_q = st.sidebar.text_input("Ask anything", key="chat_input")

ask_btn = st.sidebar.button("Ask Assistant")

if ask_btn:

    if user_q.strip():

        context = ""

        if not df.empty:
            context = df.head(5)[["Product", "Price", "Rating"]].to_string()

        answer = ask_dealgenie(user_q, context)

        st.session_state.last_answer = answer
        st.session_state.chat_history.append(("You", user_q))
        st.session_state.chat_history.append(("AI", answer))

# =========================================================
# DISPLAY LAST ANSWER (FIXED ISSUE)
# =========================================================
if st.session_state.last_answer:
    st.sidebar.markdown("### 🧠 Latest Answer")
    st.sidebar.write(st.session_state.last_answer)

# =========================================================
# CHAT HISTORY
# =========================================================
st.sidebar.markdown("### 🧾 History")

for role, msg in st.session_state.chat_history[-10:]:
    if role == "You":
        st.sidebar.markdown(f"🧑 {msg}")
    else:
        st.sidebar.markdown(f"🤖 {msg}")
