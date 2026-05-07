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
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="AI Data Generator", layout="wide")


# -----------------------------
# UI STYLE
# -----------------------------
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

.stDownloadButton > button {
    background-color: white !important;
    color: black !important;
    font-weight: 600;
    border-radius: 8px;
}

/* Top bar */
.top-bar {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:10px 5px;
}

.api-box input {
    background-color: white !important;
    color: black !important;
    border-radius: 8px;
    border: 1px solid #d1d5db !important;
}

.api-label {
    color: white;
    font-weight: 600;
    margin-right: 8px;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# TOP HEADER (API KEY RIGHT SIDE)
# -----------------------------
col1, col2 = st.columns([8, 2])

with col1:
    st.title("🧠 AI Data Generator")

with col2:
    api_key = st.text_input("🔑 API Key", type="password")


client = OpenAI(api_key=api_key) if api_key else None


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

    def clear_all(self):
        self._write([])

    def get_all(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# SCHEMA
# -----------------------------
def smart_schema(prompt):

    text = prompt.lower()

    fields = [{"name": "id", "type": "id"}]

    if "bank" in text:
        fields += [
            {"name": "name", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "amount", "type": "amount"},
            {"name": "status", "type": "string"}
        ]
    else:
        fields += [
            {"name": "name", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "status", "type": "string"}
        ]

    return fields


# -----------------------------
# DATA ENGINE
# -----------------------------
def gen_value(field):

    name = field["name"].lower()
    t = field["type"]

    if "id" in name:
        return str(uuid.uuid4())[:10]

    if "name" in name:
        return fake.name()

    if "email" in name:
        return fake.email()

    if "phone" in name:
        return "+91-" + str(random.randint(6000000000, 9999999999))

    if "status" in name:
        return random.choice(["ACTIVE", "INACTIVE", "PENDING", "SUCCESS"])

    if t == "amount":
        return round(random.uniform(100, 50000), 2)

    return "N/A"


def generate(fields, rows):

    data = []

    for _ in range(rows):
        row = {f["name"]: gen_value(f) for f in fields}
        data.append(row)

    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)

    return df


# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "record" not in st.session_state:
    st.session_state.record = None


# -----------------------------
# UI TABS
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])


# =============================
# GENERATE
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        fields = smart_schema(prompt)
        df = generate(fields, rows)

        st.session_state.df = df

        st.session_state.record = {
            "id": str(uuid.uuid4())[:8],
            "name": prompt[:40],
            "fields": fields,
            "created_at": str(datetime.now())
        }

        storage.add(st.session_state.record)

        st.success("Dataset generated")

    if st.session_state.df is not None:
        st.dataframe(st.session_state.df)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button("⬇ CSV", st.session_state.df.to_csv(index=False), "data.csv")

        with col2:
            st.download_button("⬇ JSON", json.dumps(st.session_state.record, indent=2), "data.json")


# =============================
# HISTORY
# =============================
with tab2:

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"""
        <div style="background:#111827;padding:12px;border-radius:10px;margin-bottom:10px;">
        📦 {item.get('name')}
        </div>
        """, unsafe_allow_html=True)

        fields = item.get("fields", [])

        preview = pd.DataFrame([
            {f["name"]: gen_value(f) for f in fields}
            for _ in range(3)
        ])

        preview.index = range(1, len(preview) + 1)

        st.dataframe(preview)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button("⬇ CSV", preview.to_csv(index=False), file_name=f"{item['id']}.csv")

        with col2:
            st.download_button("⬇ JSON", json.dumps(item, indent=2), file_name=f"{item['id']}.json")

        if st.button("🗑 Delete", key=item["id"]):
            storage.delete(item["id"])
            st.rerun()
