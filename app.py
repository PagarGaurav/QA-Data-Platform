import streamlit as st
import pandas as pd
import random
import json
import os
import uuid
from faker import Faker

fake = Faker()

# -----------------------------
# 🎬 NETFLIX STYLE UI
# -----------------------------
st.set_page_config(page_title="AI Data Copilot", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: #ffffff;
}

/* Netflix-style cards */
.card {
    background: #141a2e;
    padding: 15px;
    border-radius: 12px;
    margin: 10px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.title {
    font-size: 22px;
    font-weight: bold;
}

.subtitle {
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Data Copilot (Netflix Mode)")


# -----------------------------
# 🧠 STORAGE
# -----------------------------
FILE = "data.json"

def load():
    if not os.path.exists(FILE):
        return {}
    try:
        return json.load(open(FILE))
    except:
        return {}

def save(data):
    json.dump(data, open(FILE, "w"), indent=2)


# -----------------------------
# 🧠 INTELLIGENCE ENGINE
# -----------------------------
def smart_detect(prompt):

    text = prompt.lower()

    # SAP
    if "sap" in text or "vendor" in text or "purchase" in text:
        return {
            "domain": "SAP",
            "fields": [
                ("vendor", "string"),
                ("material", "string"),
                ("quantity", "int"),
                ("price", "amount"),
                ("ship_to_party", "string"),
                ("sold_to_party", "string")
            ],
            "confidence": 0.9
        }

    # HEALTH
    if "health" in text or "patient" in text:
        return {
            "domain": "HEALTH",
            "fields": [
                ("patient_name", "string"),
                ("doctor", "string"),
                ("diagnosis", "string"),
                ("hospital", "string")
            ],
            "confidence": 0.9
        }

    # BANKING
    if "bank" in text or "account" in text:
        return {
            "domain": "BANKING",
            "fields": [
                ("account", "int"),
                ("balance", "amount"),
                ("transaction", "amount")
            ],
            "confidence": 0.9
        }

    # LOGIN
    if "login" in text or "user" in text:
        return {
            "domain": "LOGIN",
            "fields": [
                ("username", "string"),
                ("email", "string"),
                ("password", "string"),
                ("status", "string")
            ],
            "confidence": 0.95
        }

    return {
        "domain": "UNKNOWN",
        "fields": None,
        "confidence": 0.2
    }


# -----------------------------
# 🧠 VALUE GENERATION
# -----------------------------
def gen_value(t):

    if t == "int":
        return random.randint(1000, 99999)

    if t == "string":
        return fake.word()

    if t == "amount":
        return round(random.uniform(100, 5000), 2)

    return fake.word()


def generate(schema):

    data = []

    for i in range(10):
        row = {}

        for col, t in schema:
            row[col] = gen_value(t)

        data.append(row)

    return pd.DataFrame(data)


# -----------------------------
# 🧠 SESSION
# -----------------------------
if "pending" not in st.session_state:
    st.session_state.pending = None


# -----------------------------
# 🎯 LAYOUT (NETFLIX STYLE)
# -----------------------------
col1, col2 = st.columns([1, 2])

# -----------------------------
# LEFT PANEL
# -----------------------------
with col1:

    st.markdown("### 🧠 AI Copilot")

    prompt = st.text_area("Describe dataset")

    if st.button("Generate"):

        result = smart_detect(prompt)
        st.session_state.pending = result

        if result["fields"] is None:

            st.error("⚠️ I cannot understand this request safely.")

            st.info("""
Try examples:
- SAP purchase order dataset  
- Health patient dataset  
- Banking account dataset  
- Login test data  
""")

        else:

            fields = ", ".join([f[0] for f in result["fields"]])

            st.success(f"""
📦 Domain: {result['domain']}  
📊 Fields: {fields}  
🎯 Confidence: {result['confidence']}  

👉 Type YES to generate
""")


# -----------------------------
# RIGHT PANEL (PREVIEW)
# -----------------------------
with col2:

    st.markdown("### 🎬 Preview Panel")

    if st.session_state.pending:

        result = st.session_state.pending

        if result["fields"] and prompt.lower().strip() == "yes":

            df = generate(result["fields"])

            st.success("Dataset Generated")

            st.dataframe(df, use_container_width=True)

            st.download_button(
                "⬇ Download CSV",
                df.to_csv(index=False),
                "dataset.csv"
            )

        elif result["fields"]:

            st.info("Waiting for confirmation → type YES")

        else:
            st.warning("No valid schema detected")


# -----------------------------
# 🎬 NETFLIX GALLERY
# -----------------------------
st.markdown("---")
st.subheader("🎬 Dataset Gallery")

data = load()

if not data:
    st.info("No datasets yet")
else:
    cols = st.columns(3)

    for i, (k, v) in enumerate(data.items()):

        with cols[i % 3]:

            st.markdown(f"""
<div class="card">
<div class="title">📦 {v.get('domain')}</div>
<div class="subtitle">{v.get('fields')}</div>
</div>
""", unsafe_allow_html=True)
