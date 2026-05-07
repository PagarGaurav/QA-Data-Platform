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

section[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator")

# -----------------------------
# API
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
# LLM COLUMN INTENT MAPPING (NEW CORE ENGINE)
# -----------------------------
COLUMN_INTENT_CACHE = {}

def get_column_intents(schema, prompt):

    cache_key = str(schema)

    if cache_key in COLUMN_INTENT_CACHE:
        return COLUMN_INTENT_CACHE[cache_key]

    system = """
You are an enterprise data architect.

Given column names, map each column to a semantic intent type.

Return ONLY JSON:
{
  "column_name": "semantic_type"
}

Allowed semantic types:
- id
- email
- phone
- person_name
- password
- role
- status
- txn_type
- balance
- age
- gender
- diagnosis
- date
- numeric_small
- numeric_large
- text
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(schema)}
        ]
    )

    raw = res.choices[0].message.content.strip()

    raw = re.sub(r"```json", "", raw)
    raw = re.sub(r"```", "", raw).strip()

    try:
        intents = json.loads(raw)
    except:
        intents = {}

    COLUMN_INTENT_CACHE[cache_key] = intents
    return intents

# -----------------------------
# DOMAIN DETECTION
# -----------------------------
def detect_domain(prompt):
    p = prompt.lower()

    if "login" in p:
        return "login"
    if "bank" in p:
        return "bank"
    if "medical" in p:
        return "medical"
    return "generic"

# -----------------------------
# SCHEMA ENGINE (UNCHANGED)
# -----------------------------
def extract_schema(prompt):

    domain = detect_domain(prompt)

    if domain == "login":
        return [
            {"name": "email", "type": "email"},
            {"name": "password", "type": "string"},
            {"name": "role", "type": "string"},
            {"name": "account_status", "type": "status"},
            {"name": "login_attempts", "type": "int"}
        ]

    if domain == "bank":
        return [
            {"name": "customer_id", "type": "id"},
            {"name": "balance", "type": "float"},
            {"name": "txn_type", "type": "string"},
            {"name": "status", "type": "status"}
        ]

    if domain == "medical":
        return [
            {"name": "patient_id", "type": "id"},
            {"name": "patient_name", "type": "string"},
            {"name": "age", "type": "int"},
            {"name": "gender", "type": "string"},
            {"name": "diagnosis", "type": "string"}
        ]

    return [
        {"name": "id", "type": "id"},
        {"name": "name", "type": "string"}
    ]

# -----------------------------
# ENTERPRISE + LLM INTENT VALUE ENGINE
# -----------------------------
def gen_value(field, intent):

    name = field["name"].lower()
    semantic = intent.get(name, "text")

    # -----------------------------
    # ID
    # -----------------------------
    if semantic == "id":
        return str(uuid.uuid4())[:10]

    # -----------------------------
    # EMAIL / PHONE
    # -----------------------------
    if semantic == "email":
        return fake.email()

    if semantic == "phone":
        return "+91" + str(random.randint(6000000000, 9999999999))

    # -----------------------------
    # PERSON
    # -----------------------------
    if semantic == "person_name":
        return fake.name()

    # -----------------------------
    # LOGIN / SECURITY
    # -----------------------------
    if semantic == "role":
        return random.choice(["ADMIN", "USER", "MANAGER"])

    if semantic == "status":
        return random.choice(["ACTIVE", "INACTIVE", "BLOCKED", "PENDING"])

    if semantic == "txn_type":
        return random.choice(["DEBIT", "CREDIT"])

    # -----------------------------
    # MEDICAL
    # -----------------------------
    if semantic == "diagnosis":
        return random.choice(["Diabetes", "Asthma", "Flu", "Infection", "Migraine"])

    if semantic == "gender":
        return random.choice(["MALE", "FEMALE", "OTHER"])

    if semantic == "age":
        return random.randint(1, 95)

    # -----------------------------
    # NUMBERS
    # -----------------------------
    if semantic == "balance":
        return round(random.uniform(100, 1000000), 2)

    if semantic == "numeric_small":
        return random.randint(1, 100)

    if semantic == "numeric_large":
        return random.randint(1000, 999999)

    # -----------------------------
    # DEFAULT TEXT
    # -----------------------------
    return fake.word()

# -----------------------------
# GENERATOR (FAST + SCALABLE)
# -----------------------------
MAX_CHUNK = 5000

def generate_data(schema, rows, prompt):

    intents = get_column_intents(schema, prompt)

    data = []
    remaining = rows

    while remaining > 0:

        batch = min(MAX_CHUNK, remaining)

        for _ in range(batch):
            row = {}
            for f in schema:
                row[f["name"]] = gen_value(f, intents)
            data.append(row)

        remaining -= batch

    return pd.DataFrame(data)

# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "record" not in st.session_state:
    st.session_state.record = None

# -----------------------------
# UI (UNCHANGED)
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])

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

        st.dataframe(df, height=500)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                df.to_csv(index=False),
                file_name=f"data_{len(df)}.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                df.to_json(orient="records"),
                file_name="data.json"
            )

with tab2:

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

        preview = pd.DataFrame([
            {f["name"]: fake.word() for f in schema}
            for _ in range(3)
        ])

        st.dataframe(preview, height=250)

        st.markdown("---")
