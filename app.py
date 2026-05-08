import streamlit as st
import pandas as pd
import requests
import re
import streamlit.components.v1 as components

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="DealGenie", layout="wide")

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
# HERO
# =========================================================
st.markdown("""
<div class="hero">
<h1>🛍 DealGenie</h1>
<h3>Smart deals. Real insights.</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SAFE STATE
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = None

if "memory" not in st.session_state:
    st.session_state.memory = {"disliked": set()}

st.session_state.memory.setdefault("disliked", set())

if "last_q" not in st.session_state:
    st.session_state.last_q = ""

if "last_a" not in st.session_state:
    st.session_state.last_a = ""

# =========================================================
# SIDEBAR
# =========================================================
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
country = st.sidebar.selectbox("Country", ["India", "US"])
max_products = st.sidebar.slider("Deals", 5, 40, 5)

query = st.text_input("🔎 Search Products")

# =========================================================
# 🎤 VOICE (CLEAN)
# =========================================================
voice_html = """
<button onclick="startVoice()" style="
background:#ff2d2d;
color:white;
padding:12px;
border:none;
border-radius:10px;
font-weight:800;
cursor:pointer;
width:100%;
font-size:16px;">
Speak
</button>

<script>
function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Voice not supported");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        const input = window.parent.document.querySelector('input[type="text"]');
        input.value = text;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    };
}
</script>
"""

st.sidebar.markdown("## 🎤")
components.html(voice_html, height=80)

# =========================================================
# INTENT DETECTION (KEY FIX)
# =========================================================
def detect_intent(q):
    q = q.lower()

    if "tshirt" in q or "t-shirt" in q:
        return "tshirt"
    if "shoe" in q or "sneaker" in q:
        return "shoes"
    if "mobile" in q:
        return "mobile"
    if "laptop" in q:
        return "laptop"

    return None


def filter_by_intent(df, intent):

    if intent is None:
        return df

    mapping = {
        "tshirt": ["tshirt", "t-shirt", "tee", "shirt"],
        "shoes": ["shoe", "sneaker", "running"],
        "mobile": ["mobile", "phone"],
        "laptop": ["laptop"]
    }

    keys = mapping.get(intent, [])

    mask = df["Product"].str.lower().apply(
        lambda x: any(k in x for k in keys)
    )

    filtered = df[mask]

    return filtered if not filtered.empty else df

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
            "Link": x.get("link"),
            "Image": x.get("thumbnail") or "https://via.placeholder.com/300",
            "price_num": price_num(x.get("price")),
            "rating_num": safe_float(x.get("rating", 0)),
            "reviews_num": reviews_num(x.get("reviews", 0))
        })

    return pd.DataFrame(items)

# =========================================================
# MEMORY FILTER
# =========================================================
def apply_memory(df):
    disliked = st.session_state.memory.get("disliked", set())

    for b in disliked:
        df = df[~df["Product"].str.lower().str.contains(b)]

    return df if not df.empty else df

# =========================================================
# AI ASSISTANT
# =========================================================
def assistant(q, df):

    if df is None or df.empty:
        return "Search products first."

    st.session_state.last_q = q

    ql = q.lower()

    # store dislikes
    brands = ["puma", "nike", "adidas"]

    for b in brands:
        if f"dont want {b}" in ql or f"don't want {b}" in ql:
            st.session_state.memory["disliked"].add(b)
            return f"🚫 Will avoid {b}"

    intent = detect_intent(q)

    df = filter_by_intent(df, intent)
    df = apply_memory(df)

    if df.empty:
        return "❌ No relevant products found."

    best = df.sort_values("price_num").iloc[0]

    return f"🔥 Best pick: {best['Product']}"

# =========================================================
# MAIN SEARCH
# =========================================================
if st.button("🚀 SEARCH DEALS"):

    if not api_key or not query:
        st.warning("Enter API key + product")
        st.stop()

    df = fetch(query)

    if df.empty:
        st.warning("No results found")
        st.stop()

    df = apply_memory(df)

    st.session_state.df = df

    best = df.iloc[0]

    st.markdown("## 🔥 Best Deal")
    st.image(best["Image"], width=300)
    st.write(best["Product"])
    st.write(best["Price"])
    st.link_button("🛒 Buy Now", best["Link"])

# =========================================================
# AI PANEL (NO HISTORY)
# =========================================================
st.sidebar.markdown("## 🤖 DealGenie AI")

ask = st.sidebar.text_input("Ask AI")

if st.sidebar.button("Ask"):
    df = st.session_state.get("df", None)
    reply = assistant(ask, df)

    st.session_state.last_a = reply

# show last only
if st.session_state.last_q:
    st.sidebar.markdown("### 🧑 You")
    st.sidebar.write(st.session_state.last_q)

if st.session_state.last_a:
    st.sidebar.markdown("### 🤖 DealGenie")
    st.sidebar.write(st.session_state.last_a)
