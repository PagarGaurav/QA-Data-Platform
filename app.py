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
# LLM SCHEMA + DATA GENERATION
# -----------------------------

def extract_schema(prompt):
    """Step 1: Ask GPT to define strict schema"""
    system = """
You are a data schema designer.
Return ONLY valid JSON.

Rules:
- output must be JSON array
- each field must have:
  name, type (string, int, float, email, phone, date, status, id)
- no explanation
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Create dataset schema for: {prompt}"}
        ]
    )

    return json.loads(res.choices[0].message.content)


def generate_data(schema, rows, prompt):
    """Step 2: Generate real valid structured data"""

    system = """
You generate ONLY valid JSON array of objects.
Rules:
- Must follow schema exactly
- No extra fields
- No null unless required
- All emails must be valid
- All phones must be Indian format +91XXXXXXXXXX
- IDs must be unique
"""

    user_prompt = f"""
Schema: {json.dumps(schema)}
Rows: {rows}
Context: {prompt}

Return JSON array only.
"""

    for _ in range(3):  # retry safety
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt}
                ]
            )

            data = json.loads(res.choices[0].message.content)

            if isinstance(data, list):
                return pd.DataFrame(data)

        except:
            continue

    raise Exception("Failed to generate valid dataset")


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
# GENERATE (UI SAME)
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        if not client:
            st.error("Please add OpenAI API key")
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

        st.dataframe(st.session_state.df)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                st.session_state.df.to_csv(index=False),
                "data.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                st.session_state.df.to_json(orient="records"),
                "data.json"
            )

# =============================
# HISTORY (UNCHANGED UI)
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

        try:
            preview = generate_data(schema, 3, item["name"])
        except:
            preview = pd.DataFrame()

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
