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
# UI
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
    font-weight: 500;
}

</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator")


# -----------------------------
# API KEY
# -----------------------------
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")

client = None
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

    def clear_all(self):
        self._write([])

    def get_all(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# GPT SCHEMA CORRECTION LAYER
# -----------------------------
def gpt_schema_correction(prompt):

    if not client:
        return None

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are a Schema Correction Engine.

Convert user request into CLEAN JSON schema.

Rules:
- Return ONLY JSON
- Each field must have:
  name (snake_case)
  type (string, int, email, phone, amount, date, id)

Infer intelligently but do not hallucinate domains.

Format:
{
  "name": "...",
  "fields": [
    {"name":"...","type":"..."}
  ]
}
"""
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(res.choices[0].message.content)

    except:
        return None


# -----------------------------
# FALLBACK SCHEMA ENGINE
# -----------------------------
def smart_infer_fields(prompt):

    text = prompt.lower()

    fields = [{"name": "id", "type": "id"}]

    if any(k in text for k in ["login", "user", "auth"]):
        fields += [
            {"name": "username", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "status", "type": "string"}
        ]

    elif any(k in text for k in ["bank", "customer", "loan"]):
        fields += [
            {"name": "name", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "address", "type": "string"},
            {"name": "amount", "type": "amount"},
            {"name": "status", "type": "string"}
        ]

    elif any(k in text for k in ["medical", "patient"]):
        fields += [
            {"name": "patient_name", "type": "string"},
            {"name": "age", "type": "int"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
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
# VALUE ENGINE (STRICT VALID DATA)
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

    if "address" in name:
        return f"{fake.building_number()} {fake.street_name()}, {fake.city()}"

    if "date" in name:
        return fake.date_between("-5y", "today").strftime("%Y-%m-%d")

    if "age" in name:
        return random.randint(18, 80)

    if "status" in name:
        return random.choice(["ACTIVE", "INACTIVE", "PENDING", "SUCCESS", "FAILED"])

    if t == "amount":
        return round(random.uniform(10, 99999), 2)

    if t == "int":
        return random.randint(1, 9999)

    return "N/A"


# -----------------------------
# GENERATE DATA
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):
        row = {}

        for f in fields:
            row[f["name"]] = gen_value(f)

        data.append(row)

    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)  # START FROM 1

    return df


# -----------------------------
# SCHEMA PIPELINE (GPT + FALLBACK)
# -----------------------------
def build_schema(prompt):

    corrected = gpt_schema_correction(prompt)

    if corrected and "fields" in corrected:
        return corrected

    return {
        "name": prompt[:30],
        "fields": smart_infer_fields(prompt)
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

        schema = build_schema(prompt)

        df = generate(schema["fields"], rows)

        st.session_state.df = df
        st.session_state.record = {
            "id": str(uuid.uuid4())[:8],
            "name": schema.get("name"),
            "fields": schema.get("fields"),
            "created_at": str(datetime.now())
        }

        storage.add(st.session_state.record)

        st.success("Dataset generated")


    if st.session_state.df is not None:

        st.markdown(f"""
        <div style="
            background:#111827;
            padding:12px;
            border-radius:10px;
            font-weight:600;
            margin-bottom:10px;">
        📦 Dataset Preview
        </div>
        """, unsafe_allow_html=True)

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
                json.dumps(st.session_state.record, indent=2),
                "data.json"
            )


# =============================
# 📂 HISTORY
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
### 📦 {item.get('name')}
ID: {item.get('id')}
""")

        if st.button("🗑 Delete", key=item["id"]):
            storage.delete(item["id"])
            st.rerun()
