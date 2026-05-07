import streamlit as st
import pandas as pd
import random
import json
import os
import uuid
from faker import Faker

fake = Faker()

# -----------------------------
# 🎬 UI THEME (Netflix SaaS)
# -----------------------------
st.set_page_config(page_title="AI Data Copilot SaaS", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: white;
}

.card {
    background: #141a2e;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Data Copilot SaaS")


# -----------------------------
# 🗂 STORAGE
# -----------------------------
FILE = "data.json"

def load():
    if not os.path.exists(FILE):
        return []
    try:
        return json.load(open(FILE))
    except:
        return []

def save(data):
    json.dump(data, open(FILE, "w"), indent=2)


# -----------------------------
# 🧠 INTELLIGENCE ENGINE
# -----------------------------
def detect(prompt):

    t = prompt.lower()

    if any(x in t for x in ["sap", "vendor", "purchase"]):
        return "SAP", [
            ("vendor", "string"),
            ("material", "string"),
            ("quantity", "int"),
            ("price", "amount"),
            ("ship_to_party", "string"),
            ("sold_to_party", "string")
        ]

    if any(x in t for x in ["health", "patient", "doctor"]):
        return "HEALTH", [
            ("patient", "string"),
            ("doctor", "string"),
            ("diagnosis", "string"),
            ("hospital", "string")
        ]

    if any(x in t for x in ["bank", "account"]):
        return "BANKING", [
            ("account", "int"),
            ("balance", "amount"),
            ("transaction", "amount")
        ]

    if any(x in t for x in ["login", "user"]):
        return "LOGIN", [
            ("username", "string"),
            ("email", "string"),
            ("password", "string"),
            ("status", "string")
        ]

    return None, None


# -----------------------------
# 🧠 VALUE ENGINE
# -----------------------------
def gen(t):

    if t == "int":
        return random.randint(1000, 99999)

    if t == "string":
        return fake.word()

    if t == "amount":
        return round(random.uniform(100, 5000), 2)

    return fake.word()


def generate(schema):
    return pd.DataFrame([
        {c: gen(t) for c, t in schema}
        for _ in range(10)
    ])


# -----------------------------
# 🗂 STORAGE WRAPPER
# -----------------------------
def add_record(obj):
    data = load()
    data.append(obj)
    save(data)


def delete_record(id):
    data = load()
    data = [x for x in data if x["id"] != id]
    save(data)


# -----------------------------
# 🧠 SESSION
# -----------------------------
if "result" not in st.session_state:
    st.session_state.result = None


# -----------------------------
# 🎯 LAYOUT
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "🎬 Dashboard"])


# =============================
# 🚀 GENERATE TAB
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")

    if st.button("Generate"):

        domain, schema = detect(prompt)

        if not schema:

            st.error("❌ Cannot understand request safely")

            st.info("""
Try:
- SAP purchase order dataset
- Health patient dataset
- Banking account dataset
- Login test users
""")

        else:

            st.session_state.result = {
                "id": str(uuid.uuid4())[:8],
                "prompt": prompt,
                "domain": domain,
                "schema": schema,
                "rows": 10
            }

            st.success(f"Detected: {domain}")

            st.info("👉 Type YES to generate dataset")


    if st.session_state.result:

        if st.text_input("Confirm (YES)") == "YES":

            df = generate(st.session_state.result["schema"])

            st.dataframe(df)

            st.download_button(
                "Download CSV",
                df.to_csv(index=False),
                "dataset.csv"
            )

            add_record(st.session_state.result)

            st.session_state.result = None


# =============================
# 🎬 DASHBOARD TAB
# =============================
with tab2:

    data = load()

    st.subheader("🎬 Dataset Gallery")

    search = st.text_input("🔎 Search")
    filter_domain = st.selectbox(
        "Filter",
        ["ALL", "SAP", "HEALTH", "BANKING", "LOGIN"]
    )

    def match(x):

        if search and search.lower() not in x["prompt"].lower():
            return False

        if filter_domain != "ALL" and x["domain"] != filter_domain:
            return False

        return True


    filtered = [x for x in data if match(x)]

    cols = st.columns(3)

    for i, item in enumerate(reversed(filtered)):

        with cols[i % 3]:

            st.markdown(f"""
<div class="card">
<h4>📦 {item['domain']}</h4>
<p>{item['prompt'][:60]}...</p>
<p><b>ID:</b> {item['id']}</p>
</div>
""", unsafe_allow_html=True)

            c1, c2 = st.columns(2)

            with c1:
                if st.button("👁 View", key="v"+item["id"]):

                    st.info("📊 Preview")
                    st.write(item["schema"])

            with c2:
                if st.button("🗑 Delete", key="d"+item["id"]):
                    delete_record(item["id"])
                    st.rerun()
