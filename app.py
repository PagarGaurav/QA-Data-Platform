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

st.set_page_config(page_title="AI DataGen SaaS", layout="wide")

DATA_FILE = "storage.json"


# -----------------------------
# 🧾 STORAGE SYSTEM (SAAS FEATURE)
# -----------------------------
def load_history():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=2, default=str)


# -----------------------------
# 🧠 SIMPLE AI INTENT ENGINE
# -----------------------------
def parse_request(prompt):
    text = prompt.lower()

    rows = 1000
    if "10k" in text:
        rows = 10000
    if "50k" in text:
        rows = 50000

    columns = []

    if "name" in text:
        columns.append(("name", "name"))
    if "email" in text:
        columns.append(("email", "email"))
    if "country" in text:
        columns.append(("country", "country"))
    if "age" in text:
        columns.append(("age", "age"))
    if "price" in text or "amount" in text:
        columns.append(("value", "amount"))

    if not columns:
        columns = [("id", "int"), ("value", "amount")]

    return rows, columns


# -----------------------------
# 🏗 DATA ENGINE
# -----------------------------
def gen_value(t):
    if t == "int":
        return random.randint(1, 10000)
    if t == "name":
        return fake.name()
    if t == "email":
        return fake.email()
    if t == "country":
        return fake.country()
    if t == "age":
        return random.randint(18, 70)
    if t == "amount":
        return round(np.random.lognormal(3, 1), 2)
    return fake.word()


def generate_df(rows, cols):
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
# 🧠 SAAS SESSION LOGIC
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = load_history()


# -----------------------------
# 🎨 UI HEADER
# -----------------------------
st.title("🧠 AI Data Generator SaaS")
st.markdown("Generate realistic datasets instantly — like a mini data platform")

tab1, tab2 = st.tabs(["🚀 Generate", "📂 My History"])


# -----------------------------
# 🚀 GENERATION PAGE
# -----------------------------
with tab1:

    prompt = st.text_area(
        "💬 Describe dataset",
        placeholder="e.g. Generate ecommerce users with name email country age 10k rows"
    )

    if st.button("Generate Dataset"):

        rows, cols = parse_request(prompt)
        df = generate_df(rows, cols)

        run_id = str(uuid.uuid4())[:8]

        st.subheader("📊 Dataset Preview")
        st.dataframe(df.head(20))

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📁 Download CSV",
            csv,
            f"dataset_{run_id}.csv",
            "text/csv"
        )

        # Save to history (SAAS feature)
        record = {
            "id": run_id,
            "prompt": prompt,
            "rows": rows,
            "columns": [c[0] for c in cols],
            "timestamp": str(datetime.now())
        }

        st.session_state.history.append(record)
        save_history(st.session_state.history)

        st.success(f"Saved run {run_id}")


# -----------------------------
# 📂 HISTORY PAGE (SAAS FEATURE)
# -----------------------------
with tab2:

    st.subheader("📁 Past Generations")

    if not st.session_state.history:
        st.info("No history yet")
    else:
        for item in reversed(st.session_state.history):

            st.markdown(f"""
### Run ID: {item['id']}
- Prompt: {item['prompt']}
- Rows: {item['rows']}
- Columns: {item['columns']}
- Time: {item['timestamp']}
""")