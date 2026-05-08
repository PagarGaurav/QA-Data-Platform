import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie Copilot AI", layout="wide")

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

.stButton > button {
    background:#ff2d2d;
    color:white;
    font-weight:800;
    border-radius:10px;
    width:100%;
}

.hero {
    background: linear-gradient(90deg,#000,rgba(0,0,0,0.3)),
    url('https://images.unsplash.com/photo-1607082349566-187342175e2f');
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
<h1>🛍 DealGenie Copilot AI</h1>
<h3>Smart shopping assistant with real decision power</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "df" not in st.session_state:
    st.session_state.df = None

if "memory" not in st.session_state:
    st.session_state.memory = {"disliked": set()}

# =========================================================
# SIDEBAR SETTINGS
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Deals shown", 5, 40, 5)

# =========================================================
# MAIN SEARCH
# =========================================================
query = st.text_input("🔎 Search Products")

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
# RENDER
# =========================================================
def row(title, items):
    st.markdown(f"## {title}")
    cols = st.columns(4)

    for i, r in enumerate(items):
        with cols[i % 4]:
            st.image(r["Image"], use_container_width=True)
            st.write(r["Product"])
            st.write(r["Price"])
            st.link_button("🛒 Buy", r["Link"])

# =========================================================
# HUMAN AI ENGINE
# =========================================================
def copilot_response(q, df):

    if df is None or df.empty:
        return "⚠️ Please search products first."

    ql = q.lower()

    # -----------------------------
    # DISLIKE BRAND MEMORY
    # -----------------------------
    brands = ["puma", "nike", "adidas", "reebok"]

    for b in brands:
        if f"dont want {b}" in ql or f"don't want {b}" in ql:
            st.session_state.memory["disliked"].add(b)
            return f"🚫 Noted: I will avoid {b} products."

    filtered = df.copy()

    for b in st.session_state.memory["disliked"]:
        filtered = filtered[~filtered["Product"].str.lower().str.contains(b)]

    if filtered.empty:
        filtered = df

    # -----------------------------
    # COMPARE
    # -----------------------------
    if "compare" in ql or "vs" in ql:
        top = filtered.sort_values("ai_score", ascending=False).head(2)

        if len(top) < 2:
            return "Not enough products to compare."

        a, b = top.iloc[0], top.iloc[1]

        return f"""
🆚 Comparison:

👉 {a['Product']} → Better overall value  
👉 {b['Product']} → Alternative option  

🏆 Winner: {a['Product']}
"""

    # -----------------------------
    # BUDGET
    # -----------------------------
    if "under" in ql or "budget" in ql:
        best = filtered.sort_values("price_num").head(3)
        return "💸 Budget picks:\n" + "\n".join(best["Product"])

    # -----------------------------
    # DEFAULT BEST
    # -----------------------------
    best = filtered.sort_values("ai_score", ascending=False).iloc[0]

    return f"🔥 Best pick: {best['Product']} ({best['Price']})"

# =========================================================
# MAIN SEARCH BUTTON
# =========================================================
if st.button("🚀 SEARCH DEALS"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query)

    if df.empty:
        st.warning("No results found")
        st.stop()

    df["ai_score"] = df.apply(ai_score, axis=1)

    st.session_state.df = df

    pool = df.sort_values("ai_score", ascending=False).head(max_products).to_dict("records")

    featured = pool.pop(0)

    st.markdown("## 🔥 Best Deal")
    st.image(featured["Image"], width=300)
    st.write(featured["Product"])
    st.write(featured["Price"])
    st.link_button("🛒 Buy Now", featured["Link"])

    row("🧠 AI Picks", pool[:2])
    row("💸 Budget", pool[2:4])
    row("⭐ Top", pool[4:6])

# =========================================================
# COPILOT PANEL (IMPORTANT FIX)
# =========================================================
st.sidebar.markdown("## 🤖 Copilot AI")

copilot_input = st.sidebar.text_input("Ask Copilot")

copilot_btn = st.sidebar.button("💬 Ask AI")

if copilot_btn and copilot_input:

    df = st.session_state.get("df", None)

    reply = copilot_response(copilot_input, df)

    st.session_state.chat.append(("you", copilot_input))
    st.session_state.chat.append(("ai", reply))

# =========================================================
# CHAT DISPLAY
# =========================================================
for r in st.session_state.chat:
    if r[0] == "you":
        st.sidebar.markdown(f"🧑 {r[1]}")
    else:
        st.sidebar.markdown(f"🤖 {r[1]}")
