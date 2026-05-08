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
st.markdown("### AI Shopping Copilot")

# =========================================================
# SIDEBAR
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
# OPENAI CLIENT (SAFE INIT)
# =========================================================
client = OpenAI(api_key=openai_key) if openai_key else None

# =========================================================
# SESSION STATE (IMPORTANT FIX)
# =========================================================
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
# AI LOGIC (UNCHANGED)
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
# 🧠 GPT COPILOT (FIXED + SAFE)
# =========================================================
def ask_dealgenie(question, context=""):

    if client is None:
        return "⚠️ Enter OpenAI API key in sidebar to enable AI Copilot."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are DealGenie AI Copilot. Help users choose products, compare them, and suggest best value options clearly."
                },
                {
                    "role": "user",
                    "content": f"{question}\n\nContext:\n{context}"
                }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ GPT Error: {str(e)}"

# =========================================================
# MAIN FLOW
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
# 💬 ASK DEALGENIE (FIXED WORKING COPILOT)
# =========================================================
st.markdown("---")
st.markdown("## 💬 Ask DealGenie (AI Copilot)")

user_q = st.text_input("Ask: compare, suggest, or decide", key="copilot_input")

if st.button("Ask AI Copilot"):

    if user_q.strip():

        context = ""

        if "df" in locals() and df is not None and not df.empty:
            context = df.head(5)[["Product", "Price", "Rating"]].to_string()

        answer = ask_dealgenie(user_q, context)

        st.session_state.chat_history.append(("You", user_q))
        st.session_state.chat_history.append(("DealGenie", answer))

# CHAT DISPLAY (PERSISTENT FIX)
for role, msg in st.session_state.chat_history:
    if role == "You":
        st.markdown(f"**🧑 You:** {msg}")
    else:
        st.markdown(f"**🤖 DealGenie:** {msg}")
