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
import re

fake = Faker()

# -----------------------------
# UI (UNCHANGED)
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

.stDownloadButton > button {
    background-color: white !important;
    color: black !important;
    font-weight: 600;
    border-radius: 8px;
}

label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator")

# -----------------------------
# API KEY
# -----------------------------
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

# -----------------------------
# CONFIG
# -----------------------------
MAX_CHUNK_SIZE = 2000  # safe batch size

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
# VALUE ENGINE (FALLBACK)
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

    if "age" in name:
        return random.randint(18, 80)

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(10, 50000), 2)

    if "status" in name:
        return random.choice(["ACTIVE", "INACTIVE", "PENDING", "SUCCESS"])

    return "N/A"

# -----------------------------
# SAFE SCHEMA GENERATION
# -----------------------------
def extract_schema(prompt):

    system = """
You are a STRICT dataset schema generator.

Return ONLY JSON array.

Rules:
- no explanation
- no markdown
- only fields: name, type
- type: string, int, float, email, phone, date, status, id
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    raw = res.choices[0].message.content.strip()

    raw = re.sub(r"```json", "", raw)
    raw = re.sub(r"```", "", raw).strip()

    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        return json.loads(raw[start:end])
    except:
        return [
            {"name": "id", "type": "id"},
            {"name": "name", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "status", "type": "status"}
        ]

# -----------------------------
# 🚀 100K SAFE STREAM GENERATOR
# -----------------------------
def generate_data(schema, rows, prompt):

    system = """
Generate ONLY valid JSON array of objects.

Rules:
- match schema exactly
- no extra fields
- valid emails
- +91 phone format
"""

    all_data = []
    remaining = rows

    while remaining > 0:

        batch_size = min(MAX_CHUNK_SIZE, remaining)

        user_prompt = f"""
Schema: {json.dumps(schema)}
Rows: {batch_size}
Context: {prompt}
Return ONLY JSON array.
"""

        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt}
                ]
            )

            raw = res.choices[0].message.content.strip()

            raw = re.sub(r"```json", "", raw)
            raw = re.sub(r"```", "", raw).strip()

            start = raw.index("[")
            end = raw.rindex("]") + 1
            batch = json.loads(raw[start:end])

            all_data.extend(batch)

        except:
            for _ in range(batch_size):
                row = {}
                for f in schema:
                    row[f["name"]] = gen_value(f)
                all_data.append(row)

        remaining -= batch_size

    return pd.DataFrame(all_data)

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
# GENERATE
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        if not client:
            st.error("Add OpenAI API key")
            st.stop()

        schema = extract_schema(prompt)
        df = generate_data(schema, rows, prompt)

        st.session_state.df = df

        st.session_state.record = {
            "id": str(uuid.uuid4())[:8],
            "name": prompt[:40],
            "schema": schema,
            "created_at": str(datetime.now())
        }

        storage.add(st.session_state.record)

        st.success("Dataset generated")

    if st.session_state.df is not None:

        df = st.session_state.df

        # IMPORTANT: UI SAFE PREVIEW ONLY
        st.dataframe(df.head(50))
        st.info(f"Showing 50 of {len(df)} rows")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                df.to_csv(index=False),
                file_name=f"data_{len(df)}_rows.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                df.to_json(orient="records"),
                file_name="data.json"
            )

# =============================
# HISTORY
# =============================
with tab2:

    colA, colB = st.columns([8, 2])

    with colB:
        if st.button("🗑 Delete All"):
            storage.clear_all()
            st.rerun()

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"""
        <div style="
            background:#111827;
            padding:12px;
            border-radius:12px;
            margin-bottom:10px;">
            <h4 style="color:white;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        schema = item.get("schema", [])

        preview = generate_data(schema, 3, item["name"])

        st.dataframe(preview)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                preview.to_csv(index=False),
                file_name=f"{item['id']}.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                preview.to_json(orient="records"),
                file_name=f"{item['id']}.json"
            )

        if st.button("🗑 Delete", key=item["id"]):
            storage.delete(item["id"])
            st.rerun()

        st.markdown("---")
