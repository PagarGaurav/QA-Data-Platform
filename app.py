import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime

fake = Faker()

# -----------------------------
# 🎨 NETFLIX STYLE UI CONFIG
# -----------------------------
st.set_page_config(page_title="AI Data Generator", layout="wide")

st.markdown("""
<style>

.stApp {
    background-color: #0b0f19;
    color: #e5e7eb;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #6366f1, #3b82f6);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.4rem 1rem;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    background-color: #111827;
    border-radius: 8px;
}

/* Card hover effect */
div[data-testid="stVerticalBlock"] > div {
    transition: transform 0.2s ease;
}

div[data-testid="stVerticalBlock"] > div:hover {
    transform: scale(1.02);
}

</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Data Generator")


# -----------------------------
# 🛡 SAFE STORAGE (PRODUCTION SAFE)
# -----------------------------
DATA_FILE = "storage.json"


class SafeStorage:

    def __init__(self, file):
        self.file = file
        self.ensure()

    def ensure(self):
        if not os.path.exists(self.file):
            self._write([])

    def _read(self):
        try:
            with open(self.file, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []

    def _write(self, data):
        tmp = self.file + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, self.file)

    def get_all(self):
        return self._read()

    def add(self, item):
        data = self._read()
        data.append(item)
        self._write(data)

    def delete(self, item_id):
        data = self._read()
        data = [x for x in data if x.get("id") != item_id]
        self._write(data)


storage = SafeStorage(DATA_FILE)


# -----------------------------
# 🧠 PARSE REQUEST
# -----------------------------
def parse_request(prompt):
    text = prompt.lower()

    rows = 1000
    if "10k" in text:
        rows = 10000
    if "50k" in text:
        rows = 50000

    cols = []

    if "name" in text:
        cols.append(("name", "name"))
    if "email" in text:
        cols.append(("email", "email"))
    if "country" in text:
        cols.append(("country", "country"))
    if "age" in text:
        cols.append(("age", "age"))
    if "price" in text or "amount" in text:
        cols.append(("value", "amount"))

    if not cols:
        cols = [("id", "int"), ("value", "amount")]

    return rows, cols


# -----------------------------
# 📧 EMAIL VALIDATION
# -----------------------------
def generate_email():
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    return fake.user_name() + "@" + random.choice(domains)


# -----------------------------
# 🏗 DATA ENGINE
# -----------------------------
def gen_value(t):
    if t == "int":
        return random.randint(1, 10000)
    if t == "name":
        return fake.name()
    if t == "email":
        return generate_email()
    if t == "country":
        return fake.country()
    if t == "age":
        return random.randint(18, 70)
    if t == "amount":
        return round(np.random.lognormal(3, 1.2), 2)
    return fake.word()


def generate_table(rows, cols):
    data = []

    for i in range(rows):
        row = {}

        for name, t in cols:
            if name == "id":
                row[name] = i + 1
            else:
                row[name] = gen_value(t)

        data.append(row)

    return pd.DataFrame(data)


# -----------------------------
# 🧾 RECORD FORMAT
# -----------------------------
def create_record(prompt, rows, cols):
    return {
        "id": str(uuid.uuid4())[:8],
        "prompt": prompt,
        "rows": rows,
        "cols": [c[0] for c in cols],
        "created_at": str(datetime.now())
    }


# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs(["🚀 Generate", "🎬 Gallery", "📊 Preview"])


# -----------------------------
# 🚀 GENERATE
# -----------------------------
with tab1:

    prompt = st.text_area("💬 Describe dataset")

    if st.button("Generate"):

        rows, cols = parse_request(prompt)
        df = generate_table(rows, cols)

        st.session_state["last_df"] = df

        record = create_record(prompt, rows, cols)
        storage.add(record)

        st.success("Dataset generated!")

        st.dataframe(df.head(20))


# -----------------------------
# 🎬 NETFLIX STYLE GALLERY
# -----------------------------
with tab2:

    st.subheader("🎬 Dataset Gallery")

    search = st.text_input("🔍 Search")

    history = storage.get_all()

    if search:
        history = [h for h in history if search.lower() in h.get("prompt", "").lower()]

    if not history:
        st.info("No datasets")
    else:

        cols_per_row = 3
        rows = [history[i:i+cols_per_row] for i in range(0, len(history), cols_per_row)]

        for row in rows:
            cols_ui = st.columns(cols_per_row)

            for i, item in enumerate(row):

                with cols_ui[i]:

                    st.markdown(f"""
<div style="
background:#111827;
padding:15px;
border-radius:12px;
border:1px solid #1f2937;
height:160px;
">

<h4 style="color:#60a5fa;">📦 Dataset</h4>

<p>{item.get('prompt','')[:40]}...</p>

<p style="color:#9ca3af;">
Rows: {item.get('rows')} <br>
Cols: {item.get('cols')}
</p>

</div>
""", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Open", key="o"+item["id"]):
                            st.session_state["view"] = item

                    with col2:
                        if st.button("🗑", key="d"+item["id"]):
                            storage.delete(item["id"])
                            st.rerun()


# -----------------------------
# 📊 PREVIEW (DETAIL VIEW)
# -----------------------------
with tab3:

    if "last_df" in st.session_state:

        df = st.session_state["last_df"]

        st.subheader("📊 Dataset Preview")

        st.dataframe(df.head(50))

        st.write("Rows:", len(df))
        st.write("Columns:", len(df.columns))
        st.write("Nulls:", int(df.isnull().sum().sum()))

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "dataset.csv"
        )

    else:
        st.info("Generate dataset first")