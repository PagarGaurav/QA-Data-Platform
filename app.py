import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# THEME
# =========================================================
st.markdown("""
<style>

.stApp {
    background: radial-gradient(circle at top,#0b0b0b,#000);
    color:white;
    font-family: Arial;
}

/* BUTTON */
.stButton > button {
    background:#ff2d2d;
    color:white;
    font-weight:800;
    border-radius:10px;
}

/* HERO */
.hero {
    background: linear-gradient(90deg,#000,rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1607082349566-187342175e2f');
    background-size:cover;
    padding:60px;
    border-radius:20px;
    margin-bottom:20px;
}

/* CARD */
.card {
    background:#111;
    border-radius:14px;
    border:1px solid #222;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart deals. Real insights. AI-powered decisions.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# INPUTS
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("How many deals?", 5, 40, 5)

query = st.text_input("Search Product")

# =========================================================
# HELPERS
# =========================================================
def price_num(x):
    nums = re.sub(r"[^\d]", "", str(x))
    return int(nums) if nums else 999999

def safe_float(x):
    try:
        return float(x)
    except:
        return 0

def reviews_num(x):
    nums = re.sub(r"[^\d]", "", str(x))
    return int(nums) if nums else 0

def ai_score(row):
    return (row["rating_num"] * 50) + (row["reviews_num"] / 100) - (row["price_num"] / 1000)

def why_buy(r):
    reasons = []
    if r["rating_num"] >= 4:
        reasons.append("Highly rated")
    if r["reviews_num"] > 500:
        reasons.append("Trusted by users")
    if r["price_num"] < 2000:
        reasons.append("Budget-friendly")
    if not reasons:
        reasons.append("Balanced choice")
    return " | ".join(reasons)

# =========================================================
# FETCH
# =========================================================
def fetch(q):

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
        items.append({
            "Product": x.get("title"),
            "Price": x.get("price"),
            "Platform": x.get("source"),
            "Rating": x.get("rating", 0),
            "Reviews": x.get("reviews", 0),
            "Link": x.get("link") or x.get("product_link"),
            "Image": x.get("thumbnail") or "https://via.placeholder.com/300",
            "price_num": price_num(x.get("price")),
            "rating_num": safe_float(x.get("rating")),
            "reviews_num": reviews_num(x.get("reviews"))
        })

    return pd.DataFrame(items)

# =========================================================
# RENDER ROW
# =========================================================
def row(title, items):

    if not items:
        return

    st.markdown(f"## {title}")
    cols = st.columns(4)

    for i, r in enumerate(items):

        with cols[i % 4]:
            st.image(r["Image"], use_container_width=True)
            st.markdown(f"### {r['Product'][:50]}")
            st.write(f"💰 {r['Price']}")
            st.write(f"⭐ {r['Rating']}")
            st.caption(why_buy(r))
            st.link_button("🛒 Buy Now", r["Link"])

# =========================================================
# AI ASSISTANT
# =========================================================
def assistant(query, df):

    q = query.lower()

    if df is None or df.empty:
        return "Search products first."

    if "vs" in q or "compare" in q:
        top = df.sort_values("ai_score", ascending=False).head(2)
        a, b = top.iloc[0], top.iloc[1]
        return f"""
🆚 Comparison:

👉 {a['Product']} (Better overall value)
👉 {b['Product']} (Cheaper option)

🏆 Winner: {a['Product']}
"""

    if "under" in q or "budget" in q:
        best = df.sort_values("price_num").head(3)
        text = "💸 Budget Picks:\n"
        for _, r in best.iterrows():
            text += f"- {r['Product']} ({r['Price']})\n"
        return text

    best = df.sort_values("ai_score", ascending=False).iloc[0]
    return f"🔥 Best: {best['Product']} ({best['Price']})"

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Discover Smart Deals"):

    if not api_key or not query:
        st.warning("Enter API key and product")
        st.stop()

    df = fetch(query)

    if df.empty:
        st.warning("No results found")
        st.stop()

    df["ai_score"] = df.apply(ai_score, axis=1)

    # STRICT LIMIT
    pool = df.sort_values("ai_score", ascending=False).head(max_products).to_dict("records")

    featured = pool.pop(0)

    st.markdown("## 🔥 Best Deal Today")
    st.image(featured["Image"], width=300)
    st.write(featured["Product"])
    st.write(featured["Price"])
    st.link_button("🛒 Buy Now", featured["Link"])

    ai_rec = pool[:2]
    pool = pool[2:]

    budget = pool[:2]
    pool = pool[2:]

    top = pool[:1]
    pool = pool[1:]

    trending = pool[:1]

    row("🧠 AI Picks", ai_rec)
    row("💸 Budget Deals", budget)
    row("⭐ Top Rated", top)
    row("🔥 Trending", trending)

    # =====================================================
    # AI CHAT
    # =====================================================
    st.markdown("---")
    st.markdown("## 💬 Ask DealGenie AI Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    user_q = st.text_input("Ask: best under 1000 / compare / worth it?")

    if user_q:
        reply = assistant(user_q, df)
        st.session_state.chat.append(("you", user_q))
        st.session_state.chat.append(("ai", reply))

    for r in st.session_state.chat:
        if r[0] == "you":
            st.markdown(f"🧑 **You:** {r[1]}")
        else:
            st.markdown(f"🤖 **AI:** {r[1]}")
