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
# 🎨 UI CONFIG
# -----------------------------
st.set_page_config(page_title="AI Data Generator", layout="wide")

st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.stApp {
    background-color: #0e1117;
}
[data-testid="stMetricValue"] {
    color: #4cc9f0;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator SaaS")

DATA_FILE = "storage.json"


# -----------------------------
# 🧾 STORAGE
# -----------------------------
def load_history():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=2, default=str)


if "history" not in st.session_state:
    st.session_state.history = load_history()


# -----------------------------
# 🧠 SMART PARSER
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
# 🧠 REALISTIC DATA ENGINE (UPGRADED)
# -----------------------------
def generate_email(name=None):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    base = fake.user_name()
    return f"{base}@{random.choice(domains)}"


def gen_value(t, context=None):
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
        # realistic distribution (small majority, few large values)
        return round(np.random.lognormal(3, 1.2), 2)

    return fake.word()


# -----------------------------
# 🏗 DATA GENERATOR
# -----------------------------
def generate_table(rows, cols):
    data = []

    for i in range(rows):
        row = {}

        for name, t in cols:
            if name == "id":
                row[name] = i + 1  # ✔ starts from 1
            else:
                row[name] = gen_value(t)

        data.append(row)

    return pd.DataFrame(data)


# -----------------------------
# 📊 DATASET SUMMARY DASHBOARD
# -----------------------------
def show_summary(df):
    st.subheader("📊 Dataset Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Rows", len(df))
    col2.metric("Columns", len(df.columns))
    col3.metric("Null Values", int(df.isnull().sum().sum()))

    st.write("### Column Types")
    st.write(df.dtypes)


# -----------------------------
# 🔍 SEARCH PROJECTS
# -----------------------------
def search_history(query):
    return [
        h for h in st.session_state.history
        if query.lower() in h["prompt"].lower()
    ]


# -----------------------------
# 🎨 UI TABS
# -----------------------------
tab1, tab2 = st.tabs(["🚀 New Project", "📂 Projects"])


# -----------------------------
# 🚀 NEW PROJECT
# -----------------------------
with tab1:

    prompt = st.text_area(
        "💬 Describe dataset",
        placeholder="Generate ecommerce users with name email age country 10k rows"
    )

    if st.button("🚀 Generate Dataset"):

        with st.spinner("🧠 AI Engine is generating dataset..."):
            rows, cols = parse_request(prompt)
            df = generate_table(rows, cols)

        run_id = str(uuid.uuid4())[:8]

        st.success("Dataset generated!")

        st.subheader("📊 Preview")
        st.dataframe(df.head(20))

        show_summary(df)

        # ---------------- EXPORTS ----------------
        csv = df.to_csv(index=False).encode("utf-8")
        json_data = df.to_json(orient="records")
        excel = df.to_excel("temp.xlsx", index=False)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button("📁 CSV", csv, f"{run_id}.csv", "text/csv")

        with col2:
            st.download_button("📁 JSON", json_data, f"{run_id}.json")

        with col3:
            df.to_excel("temp.xlsx", index=False)
            with open("temp.xlsx", "rb") as f:
                st.download_button("📁 Excel", f, f"{run_id}.xlsx")

        # save history
        record = {
            "id": run_id,
            "prompt": prompt,
            "rows": rows,
            "cols": [c[0] for c in cols],
            "time": str(datetime.now())
        }

        st.session_state.history.append(record)
        save_history(st.session_state.history)


# -----------------------------
# 📂 PROJECTS (HISTORY + SEARCH)
# -----------------------------
with tab2:

    st.subheader("📂 Projects")

    search = st.text_input("🔍 Search projects")

    history = st.session_state.history

    if search:
        history = search_history(search)

    if not history:
        st.info("No projects found")
    else:
        for item in reversed(history):

            with st.container():

                st.markdown(f"""
### 🧾 {item['id']}
- Prompt: {item['prompt']}
- Rows: {item['rows']}
- Columns: {item['cols']}
- Time: {item['time']}
""")

                if st.button(f"🗑 Delete {item['id']}", key=item["id"]):
                    st.session_state.history = [
                        h for h in st.session_state.history if h["id"] != item["id"]
                    ]
                    save_history(st.session_state.history)
                    st.rerun()
