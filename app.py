import streamlit as st
import pandas as pd
import requests
import re
import os
from openai import OpenAI

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# UI (UNCHANGED)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: #0b0b0b;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #111 !important;
}

section[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

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
st.markdown("### AI Shopping Copilot System")

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
# OPENAI CLIENT (COPILOT)
# =========================================================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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
# LIGHT AI (UNCHANGED LOGIC STYLE)
# =========================================================
def detect_intent(q):
    q = q.lower()
    if "cheap" in q or "budget" in q:
        return "BUDGET"
    elif "best" in q or "premium" in q:
        return "QUALITY"
    return "BALANCED"


def rank(df, intent):

    df = df.copy()

    df["PriceNum"] = pd.to_numeric(df["PriceNum"], errors="coerce").fillna(0)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)

    max_price = df["PriceNum"].max() or 1

    df["price_score"] = 1 - (df["PriceNum"] / max_price)
    df["rating_score"] = df["Rating"] / 5

    if intent == "BUDGET":
        w1, w2 = 0.75, 0.25
    elif intent == "QUALITY":
        w1, w2 = 0.3, 0.7
    else:
        w1, w2 = 0.55, 0.45

    df["AI_Score"] = (df["price_score"] * w1 + df["rating_score"] * w2) * 100

    return df.sort_values("AI_Score", ascending=False)

# =========================================================
# 🧠 GPT COPILOT FUNCTION
# =========================================================
def ask_dealgenie(question, context=""):

    system_prompt = """
You are DealGenie AI Shopping Copilot.

Rules:
- Help users decide what to buy
- Compare products if needed
- Be short, clear, and practical
- Focus on price, rating, and value
"""

    user_prompt = f"""
User question: {question}

Context (top products):
{context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content

# =========================================================
# MAIN FLOW (UNCHANGED CORE LOGIC)
# =========================================================
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

    intent = detect_intent(query)

    df = rank(df, intent)
    df = df.head(max_products)

    st.markdown("## 🔥 AI Recommended Products")

    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.image(r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                         use_container_width=True)

                st.markdown(f"**{r['Product']}**")

                st.write(f"💰 {r['Price']}")

                st.write(f"⭐ {r['Rating']}")

                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)

# =========================================================
# 💬 ASK DEALGENIE (GPT COPILOT UI - NO CHANGE TO MAIN UI)
# =========================================================
st.markdown("---")
st.markdown("## 💬 Ask DealGenie (AI Copilot)")

user_q = st.text_input("Ask anything: compare, suggest, or decide")

if st.button("Ask AI Copilot"):

    if user_q:

        context = ""

        if "df" in locals() and not df.empty:
            context = df.head(3)[["Product", "Price", "Rating"]].to_string()

        answer = ask_dealgenie(user_q, context)

        st.session_state.chat_history.append(("You", user_q))
        st.session_state.chat_history.append(("DealGenie AI", answer))

# CHAT DISPLAY
for role, msg in st.session_state.chat_history:
    if role == "You":
        st.markdown(f"**🧑 You:** {msg}")
    else:
        st.markdown(f"**🤖 DealGenie AI:** {msg}")
