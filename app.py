import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG (UNCHANGED BRANDING)
# =========================================================
st.set_page_config(page_title="DealGenie AI Shopping", layout="wide")

# =========================================================
# YOUR ORIGINAL THEME (PRESERVED)
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

.card {
    background:#111;
    border-radius:14px;
    padding:10px;
    border:1px solid #222;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO (UNCHANGED BRAND)
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie AI Shopping</h1>
<h3>Smart recommendations. Real savings.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SAFE STATE
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = None

# =========================================================
# INTENT DETECTION (ONLY AI UPGRADE)
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
# RELEVANCE FILTER (SMART BUT SAFE)
# =========================================================
def is_relevant(title, intent):

    t = str(title).lower()

    mapping = {
        "tshirt": ["tshirt", "t-shirt", "tee", "shirt", "polo"],
        "shoes": ["shoe", "sneaker", "running"],
        "mobile": ["mobile", "phone"],
        "laptop": ["laptop"]
    }

    keywords = mapping.get(intent, [])

    if not keywords:
        return True

    return any(k in t for k in keywords)

# =========================================================
# FETCH (UNCHANGED)
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
        items.append({
            "Product": x.get("title"),
            "Price": x.get("price"),
            "Link": x.get("link"),
            "Image": x.get("thumbnail"),
            "price_num": int(re.sub(r"[^\d]", "", str(x.get("price") or 999999)) or 999999)
        })

    return pd.DataFrame(items)

# =========================================================
# AI ENGINE (ONLY LOGIC UPGRADE)
# =========================================================
def smart_pick(df, query):

    intent = detect_intent(query)

    df = df[df["Product"].apply(lambda x: is_relevant(x, intent))]

    if df.empty:
        return None, intent

    best = df.sort_values("price_num").iloc[0]

    return best, intent

# =========================================================
# INPUTS
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])

query = st.text_input("🔎 Search Product")

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 Start AI Shopping"):

    if not api_key or not query:
        st.warning("Enter API key and product")
        st.stop()

    df = fetch(query, api_key, country)

    best, intent = smart_pick(df, query)

    st.session_state.df = df

    # =====================================================
    # KEEP YOUR ORIGINAL DISPLAY STYLE
    # =====================================================
    st.markdown("## 🔥 Best Deal")

    if best is not None:

        st.image(best["Image"], width=300)
        st.markdown(f"### {best['Product']}")
        st.write(best["Price"])

        st.markdown(f"🧠 Detected Intent: **{intent}**")

        st.link_button("🛒 Buy Now", best["Link"])

    else:
        st.warning("No relevant products found")
