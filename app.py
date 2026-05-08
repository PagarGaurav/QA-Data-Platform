import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie Human AI", layout="wide")

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
# MEMORY (HUMAN BEHAVIOR ENGINE)
# =========================================================
if "memory" not in st.session_state:
    st.session_state.memory = {
        "disliked_brands": set(),
        "liked_brands": set()
    }

if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================================================
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie Human AI</h1>
<h3>It remembers your taste. It thinks like a shopper.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR AI
# =========================================================
st.sidebar.markdown("## 💬 AI Assistant")

api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Deals shown", 5, 40, 5)

query = st.text_input("Search Product")

user_q = st.sidebar.text_input("Ask AI (compare / budget / dislike brand)")

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
# FETCH DATA
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
# HUMAN FILTER ENGINE
# =========================================================
def apply_memory_filter(df):

    disliked = st.session_state.memory["disliked_brands"]

    if not disliked:
        return df

    filtered = df.copy()

    for b in disliked:
        filtered = filtered[~filtered["Product"].str.lower().str.contains(b)]

    return filtered if not filtered.empty else df

# =========================================================
# WHY BUY (HUMAN STYLE)
# =========================================================
def why_buy(r):
    if r["rating_num"] >= 4.3:
        return "Trusted by most buyers"
    if r["reviews_num"] > 1000:
        return "Very popular choice"
    if r["price_num"] < 2000:
        return "Great value for money"
    return "Balanced product choice"

# =========================================================
# HUMAN AI ENGINE
# =========================================================
def ai_reply(q, df):

    if df is None or df.empty:
        return "Search products first."

    ql = q.lower()

    # -----------------------------
    # MEMORY UPDATE (DISLIKE BRAND)
    # -----------------------------
    brands = ["puma", "nike", "adidas", "reebok", "bata", "woodland"]

    for b in brands:
        if f"don't want {b}" in ql or f"dont want {b}" in ql:
            st.session_state.memory["disliked_brands"].add(b)
            return f"🚫 Got it. I will avoid {b} products from now."

    # -----------------------------
    # APPLY MEMORY FILTER
    # -----------------------------
    df = apply_memory_filter(df)

    # -----------------------------
    # COMPARE MODE
    # -----------------------------
    if "vs" in ql or "compare" in ql:
        top = df.sort_values("ai_score", ascending=False).head(2)

        if len(top) < 2:
            return "Not enough products to compare."

        a, b = top.iloc[0], top.iloc[1]

        return f"""
🆚 Human-style comparison:

👉 {a['Product']}
✔ Better overall value

👉 {b['Product']}
✔ Alternative option

🏆 I recommend: {a['Product']}
Because it balances price + trust + rating better.
"""

    # -----------------------------
    # BUDGET MODE
    # -----------------------------
    if "under" in ql or "budget" in ql:
        best = df.sort_values("price_num").head(3)
        return "💸 Best budget picks:\n" + "\n".join(best["Product"])

    # -----------------------------
    # GENERAL BEST PICK
    # -----------------------------
    best = df.sort_values("ai_score", ascending=False).iloc[0]

    return f"""
🔥 Best human recommendation:

👉 {best['Product']}
💰 {best['Price']}
⭐ {best['Rating']}

🧠 Reason:
{why_buy(best)}

I avoided your disliked brands and picked best value option.
"""

# =========================================================
# MAIN APP
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

    df = apply_memory_filter(df)

    pool = df.sort_values("ai_score", ascending=False).head(max_products).to_dict("records")

    featured = pool.pop(0)

    st.markdown("## 🔥 Best Deal Today")
    st.image(featured["Image"], width=300)
    st.write(featured["Product"])
    st.write(featured["Price"])
    st.caption(why_buy(featured))
    st.link_button("🛒 Buy Now", featured["Link"])

    # split
    ai = pool[:2]
    pool = pool[2:]

    budget = pool[:2]
    pool = pool[2:]

    top = pool[:1]
    pool = pool[1:]

    trend = pool[:1]

    def row(title, items):
        st.markdown(f"## {title}")
        cols = st.columns(4)
        for i, r in enumerate(items):
            with cols[i % 4]:
                st.image(r["Image"], use_container_width=True)
                st.write(r["Product"])
                st.write(r["Price"])
                st.caption(why_buy(r))
                st.link_button("Buy", r["Link"])

    row("🧠 AI Picks", ai)
    row("💸 Budget", budget)
    row("⭐ Top", top)
    row("🔥 Trending", trend)

    st.session_state.df = df

# =========================================================
# SIDEBAR AI CHAT
# =========================================================
if user_q:

    df = st.session_state.get("df", None)
    reply = ai_reply(user_q, df)

    st.session_state.chat.append(("you", user_q))
    st.session_state.chat.append(("ai", reply))

# display chat
for r in st.session_state.chat:
    if r[0] == "you":
        st.sidebar.markdown(f"🧑 {r[1]}")
    else:
        st.sidebar.markdown(f"🤖 {r[1]}")
