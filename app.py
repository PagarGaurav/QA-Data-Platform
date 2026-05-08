import streamlit as st
import pandas as pd
import requests
import re

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie AI Brain", layout="wide")

# =========================================================
# UI
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
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🧠 DealGenie AI Brain</h1>
<h3>Real intelligent shopping system</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# STATE
# =========================================================
if "memory" not in st.session_state:
    st.session_state.memory = {"disliked": set()}

# =========================================================
# INTENT DETECTION (IMPROVED)
# =========================================================
def detect_intent(q):
    q = q.lower()

    if any(x in q for x in ["tshirt", "t-shirt", "tee"]):
        return "tshirt"
    if any(x in q for x in ["shoe", "sneaker", "running", "footwear"]):
        return "shoes"
    if "mobile" in q or "phone" in q:
        return "mobile"
    if "laptop" in q:
        return "laptop"

    return "generic"

# =========================================================
# SEMANTIC RELEVANCE SCORE (CORE UPGRADE)
# =========================================================
def relevance_score(title, intent):

    t = str(title).lower()

    intent_keywords = {
        "tshirt": ["tshirt", "t-shirt", "tee", "shirt", "polo"],
        "shoes": ["shoe", "sneaker", "running", "trainer"],
        "mobile": ["mobile", "phone", "smartphone"],
        "laptop": ["laptop", "notebook"]
    }

    keywords = intent_keywords.get(intent, [])

    if not keywords:
        return 0.5  # neutral

    score = 0

    for k in keywords:
        if k in t:
            score += 1

    return score / len(keywords)

# =========================================================
# FETCH
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
            "price_num": int(re.sub(r"[^\d]", "", str(x.get("price") or 999999)) or 999999),
            "rating": float(x.get("rating") or 0),
            "reviews": int(re.sub(r"[^\d]", "", str(x.get("reviews") or 0)) or 0)
        })

    return pd.DataFrame(items)

# =========================================================
# SMART AI SCORE (REAL RANKING ENGINE)
# =========================================================
def ai_score(row, intent):

    relevance = relevance_score(row["Product"], intent)

    price_score = max(0, 1 - row["price_num"] / 10000)
    rating_score = row["rating"] / 5
    review_score = min(row["reviews"] / 1000, 1)

    return (
        (relevance * 0.5) +
        (rating_score * 0.2) +
        (review_score * 0.2) +
        (price_score * 0.1)
    )

# =========================================================
# ASSISTANT ENGINE
# =========================================================
def assistant(q, df):

    intent = detect_intent(q)

    # FILTER BY INTENT (STRICT)
    df = df[df["Product"].apply(lambda x: relevance_score(x, intent) > 0)]

    if df.empty:
        return "❌ No relevant products found"

    # RANKING
    df["score"] = df.apply(lambda r: ai_score(r, intent), axis=1)

    best = df.sort_values("score", ascending=False).iloc[0]

    return f"""
🧠 AI Recommendation

👉 {best['Product']}
💰 {best['Price']}

💡 Why:
- Matches your intent: {intent}
- Best balance of relevance + rating + value
"""

# =========================================================
# INPUTS
# =========================================================
api_key = st.sidebar.text_input("API Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])

query = st.text_input("🔎 Search anything")

# =========================================================
# MAIN
# =========================================================
if st.button("🚀 SEARCH"):

    if not api_key or not query:
        st.warning("Enter API key + query")
        st.stop()

    df = fetch(query, api_key, country)

    intent = detect_intent(query)

    st.write("Detected Intent:", intent)

    result = assistant(query, df)

    st.markdown("## 🤖 AI Result")
    st.write(result)
