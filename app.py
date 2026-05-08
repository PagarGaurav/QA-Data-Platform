import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# THEME (UNCHANGED)
# =========================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top,#0b0b0b,#000);
    color:white;
    font-family: Arial;
}

.stButton > button {
    background:#ff2d2d;
    color:white;
    font-weight:800;
    border-radius:10px;
}

.hero {
    background: linear-gradient(90deg,#000,rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1518770660439-4636190af475');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart recommendations. Real savings.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = None

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown("## 🎛 Filters")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Max Products", 5, 40, 10)

min_price = st.sidebar.number_input("Min Price", 0)
max_price = st.sidebar.number_input("Max Price", 100000)

query = st.text_input("🔎 Search Product")

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

    results = data.get("shopping_results", [])[:50]

    items = []

    for x in results:
        price_text = x.get("price") or "0"
        price_num = int(re.sub(r"[^\d]", "", str(price_text)) or 0)

        items.append({
            "Product": x.get("title"),
            "Price": price_text,
            "PriceNum": price_num,
            "Link": x.get("link"),
            "Image": x.get("thumbnail"),
            "Reviews": int(re.sub(r"[^\d]", "", str(x.get("reviews") or 0)) or 0)
        })

    return pd.DataFrame(items)

# =========================================================
# FILTERS
# =========================================================
def apply_filters(df):

    if df is None or df.empty:
        return df

    df = df[(df["PriceNum"] >= min_price) & (df["PriceNum"] <= max_price)]

    return df

# =========================================================
# INTENT DETECTION
# =========================================================
def detect_intent(q):

    q = q.lower()

    if any(x in q for x in ["tshirt", "t-shirt", "tee"]):
        return "tshirt"
    if any(x in q for x in ["shoe", "sneaker", "running"]):
        return "shoes"
    if "mobile" in q:
        return "mobile"
    if "laptop" in q:
        return "laptop"

    return "generic"

# =========================================================
# RELEVANCE CHECK
# =========================================================
def is_relevant(title, intent):

    t = str(title).lower()

    mapping = {
        "tshirt": ["tshirt", "t-shirt", "tee", "shirt", "polo"],
        "shoes": ["shoe", "sneaker", "running"],
        "mobile": ["mobile", "phone"],
        "laptop": ["laptop"]
    }

    keys = mapping.get(intent, [])

    if not keys:
        return True

    return any(k in t for k in keys)

# =========================================================
# GPT STYLE EXPLANATION LAYER
# =========================================================
def explain(row, intent, query):

    q = query.lower()
    reasons = []

    reasons.append(f"Matches intent: {intent}")

    if row["PriceNum"] < 1000:
        reasons.append("Budget-friendly option")
    elif row["PriceNum"] < 3000:
        reasons.append("Balanced price-performance")
    else:
        reasons.append("Premium quality category")

    if row["Reviews"] > 1000:
        reasons.append("Highly trusted by buyers")

    if "best" in q:
        reasons.append("You asked for best option, not cheapest")

    return " | ".join(reasons)

# =========================================================
# COMPARISON MODE
# =========================================================
def compare(df, q):

    q = q.lower()
    brands = ["nike", "puma", "adidas", "reebok"]

    found = [b for b in brands if b in q]

    if len(found) < 2:
        return None

    b1, b2 = found[:2]

    g1 = df[df["Product"].str.lower().str.contains(b1)]
    g2 = df[df["Product"].str.lower().str.contains(b2)]

    if g1.empty or g2.empty:
        return None

    p1 = g1.sort_values("PriceNum").iloc[0]
    p2 = g2.sort_values("PriceNum").iloc[0]

    winner = b1 if p1["Reviews"] >= p2["Reviews"] else b2

    return f"""
🆚 Comparison: {b1.upper()} vs {b2.upper()}

📦 {b1.title()} → {p1['Product']} ({p1['Price']})
📦 {b2.title()} → {p2['Product']} ({p2['Price']})

🏆 Winner: {winner.upper()}
💡 Reason: Better trust + popularity balance
"""

# =========================================================
# AI ENGINE
# =========================================================
def assistant(q, df):

    intent = detect_intent(q)

    comp = compare(df, q)
    if comp:
        return comp

    df = df[df["Product"].apply(lambda x: is_relevant(x, intent))]

    if df.empty:
        return "❌ No relevant products found."

    best = df.sort_values("PriceNum").iloc[0]

    return f"""
🔥 Best Pick:
👉 {best['Product']}
💰 {best['Price']}

🧠 Why this is better for YOU:
{explain(best, intent, q)}
"""

# =========================================================
# SAFE BUTTON
# =========================================================
def safe_buy(url):

    if not url:
        st.button("🛒 No Link Available", disabled=True)
    else:
        st.link_button("🛒 Buy Now", url)

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Search Product"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query, api_key, country)

    df = apply_filters(df)

    st.session_state.df = df

    if df.empty:
        st.warning("No products found")
        st.stop()

    best = df.sort_values("PriceNum").iloc[0]

    st.markdown("## 🔥 Best Deal")

    st.image(best["Image"], width=300)
    st.markdown(f"### {best['Product']}")
    st.write(best["Price"])

    safe_buy(best["Link"])

    # AI OUTPUT
    st.markdown("## 🤖 AI Insight")
    st.write(assistant(query, df))
