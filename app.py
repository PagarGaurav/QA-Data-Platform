import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime
from openai import OpenAI

fake = Faker()

# -----------------------------
# 🎨 UI
# -----------------------------
st.set_page_config(page_title="AI Data Generator", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: #e5e7eb;
}

.stButton > button {
    background: linear-gradient(90deg, #6366f1, #3b82f6);
    color: white;
    border-radius: 10px;
}

.card {
    background: #111827;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 12px;
    border: 1px solid #1f2937;
}

.title {
    font-size: 16px;
    font-weight: 600;
}

.meta {
    font-size: 12px;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator")


# -----------------------------
# 🔑 API KEY
# -----------------------------
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)


# -----------------------------
# STORAGE
# -----------------------------
DATA_FILE = "storage.json"

class Storage:

    def __init__(self, file):
        self.file = file
        if not os.path.exists(file):
            self._write([])

    def _read(self):
        try:
            with open(self.file, "r") as f:
                return json.load(f)
        except:
            return []

    def _write(self, data):
        tmp = self.file + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.file)

    def add(self, item):
        data = self._read()
        data.append(item)
        self._write(data)

    def delete(self, item_id):
        data = self._read()
        data = [x for x in data if x.get("id") != item_id]
        self._write(data)

    def get_all(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# AI SCHEMA ENGINE
# -----------------------------
def ai_schema(prompt):

    if not api_key:
        st.error("Enter API key")
        st.stop()

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
Return ONLY JSON:
{
  "name": "...",
  "domain": "...",
  "fields": [
    {"name":"...","type":"string|int|amount|email"}
  ]
}
No explanation.
"""
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(res.choices[0].message.content)


# -----------------------------
# VALUE ENGINE
# -----------------------------
def gen_value(t):

    if t == "int":
        return random.randint(1000, 99999)
    if t == "string":
        return fake.word()
    if t == "amount":
        return round(np.random.uniform(10, 5000), 2)
    if t == "email":
        return fake.email()

    return fake.word()


def generate(fields, rows):
    return pd.DataFrame([
        {f["name"]: gen_value(f["type"]) for f in fields}
        for _ in range(rows)
    ])


# -----------------------------
# VERSIONING
# -----------------------------
def get_version(data, name):
    return f"v{len([x for x in data if x.get('name') == name]) + 1}"


def create_record(prompt, schema, data_store):

    return {
        "id": str(uuid.uuid4())[:8],
        "name": schema.get("name", "Dataset"),
        "domain": schema.get("domain", "unknown"),
        "version": get_version(data_store, schema.get("name", "Dataset")),
        "fields": schema.get("fields", []),
        "created_at": str(datetime.now())
    }


# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "record" not in st.session_state:
    st.session_state.record = None


# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])


# =============================
# 🚀 GENERATE
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        schema = ai_schema(prompt)

        df = generate(schema["fields"], rows)

        st.session_state.df = df
        st.session_state.record = create_record(prompt, schema, storage.get_all())

        storage.add(st.session_state.record)

        st.success(f"{schema['name']} generated")


    # -----------------------------
    # OUTPUT
    # -----------------------------
    if st.session_state.df is not None:

        st.markdown("### 📊 Generated Dataset")
        st.dataframe(st.session_state.df)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("👁 View Schema"):
                st.json({
                    "name": st.session_state.record["name"],
                    "domain": st.session_state.record["domain"],
                    "version": st.session_state.record["version"],
                    "fields": st.session_state.record["fields"]
                })

        with col2:
            st.download_button(
                "⬇ CSV",
                st.session_state.df.to_csv(index=False),
                "dataset.csv"
            )

        with col3:
            st.download_button(
                "⬇ JSON",
                json.dumps(st.session_state.record, indent=2),
                "dataset.json"
            )

        if st.button("🗑 Delete Last"):
            storage.delete(st.session_state.record["id"])
            st.session_state.df = None
            st.session_state.record = None
            st.rerun()


# =============================
# 📂 HISTORY (CLEAN CARDS)
# =============================
with tab2:

    st.subheader("📂 Dataset History")

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        fields_preview = ", ".join(
            [f["name"] for f in item.get("fields", [])]
        )

        st.markdown(f"""
<div class="card">
    <div class="title">📦 {item.get('name')} ({item.get('version')})</div>
    <div class="meta">Domain: {item.get('domain')} | ID: {item.get('id')}</div>
    <div class="meta">Fields: {fields_preview}</div>
</div>
""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                pd.DataFrame([item]).to_csv(index=False),
                file_name=f"{item['id']}.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                json.dumps(item, indent=2),
                file_name=f"{item['id']}.json"
            )

        if st.button("🗑 Delete", key=item["id"]):
            storage.delete(item["id"])
            st.rerun()
