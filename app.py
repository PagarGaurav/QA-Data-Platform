import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

# =========================================================
# UI THEME (UNCHANGED)
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

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white !important;
}

section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

/* BUTTON */
.stButton > button {
    background-color: #ff2d2d !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
}

/* CARD FIX (uniform size) */
.card {
    height: 450px;
    background: #141414;
    border-radius: 12px;
    padding: 10px;
    border: 1px solid #222;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card img {
    height: 220px;
    width: 100%;
    object-fit: cover;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SaaS AI SERVICE LAYER (INDUSTRY STYLE)
# =========================================================
class DealGenieAIService:

    def detect_intent(self, query):
        q = query.lower()
        if any(x in q for x in ["cheap", "budget", "low price"]):
            return "BUDGET"
        elif any(x in q for x in ["best", "top", "premium"]):
            return "QUALITY"
        elif "vs" in q:
            return "COMPARISON"
        return "BALANCED"

    def rank(self, df, intent):

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

        def label(x):
            if x >= 80:
                return "🔥 Best Deal"
            elif x >= 60:
                return "👍 Good Deal"
            elif x >= 40:
                return "⚖️ Average"
            else:
                return "⚠️ Overpriced"

        df["AI_Label"] = df["AI_Score"].apply(label)

        return df.sort_values("AI_Score", ascending=False)

    def detect_anomalies(self, df):

        mean = df["PriceNum"].mean()

        def flag(x):
            if x > mean * 1.8:
                return "🚨 Overpriced"
            elif x < mean * 0.4:
                return "⚠️ Suspicious"
            return "Normal"

        df["Anomaly"] = df["PriceNum"].apply(flag)

        return df

    def explain(self, row):

        reasons = []

        if row["price_score"] > 0.7:
            reasons.append("Low price advantage")
        if row["rating_score"] > 0.8:
            reasons.append("High rating")
        if row["PriceNum"] < 3000:
            reasons.append("Budget-friendly")

        return " | ".join(reasons) if reasons else "Standard pick"


ai = DealGenieAIService()

# =========================================================
# HERO
# =========================================================
st.markdown("# 🛍 DealGenie")
st.markdown("### AI Shopping Intelligence SaaS System")

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
# MAIN PIPELINE
# =========================================================
if search_btn:

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    if df.empty:
        st.warning("No results found")
        st.stop()

    # FILTER
    df = df[
        (df["PriceNum"] >= price_range[0]) &
        (df["PriceNum"] <= price_range[1])
    ]

    # ============================
    # AI SaaS PIPELINE
    # ============================
    intent = ai.detect_intent(query)

    df = ai.rank(df, intent)
    df = ai.detect_anomalies(df)

    df = df.head(max_products)

    st.markdown("## 🔥 AI Ranked Deals")

    # =====================================================
    # STABLE GRID
    # =====================================================
    for i in range(0, len(df), 4):

        cols = st.columns(4)
        chunk = df.iloc[i:i+4]

        for col, (_, r) in zip(cols, chunk.iterrows()):

            with col:

                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.image(r["Image"] if r["Image"] else "https://via.placeholder.com/300",
                         use_container_width=True)

                st.markdown(f"**{r['Product']}**")

                st.write(f"💰 {r['Price']}")

                st.write(f"{r['AI_Label']}")

                st.caption(f"🧠 {ai.explain(r)}")

                if r["Link"]:
                    st.link_button("🛒 Buy Now", r["Link"])
                else:
                    st.button("No Link", disabled=True)

                st.markdown('</div>', unsafe_allow_html=True)
