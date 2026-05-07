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
# DOMAIN MODELS (ENTERPRISE)
# -----------------------------
LOGIN_FIELDS = {
    "email": "email",
    "password": "string",
    "role": "string",
    "account_status": "status",
    "login_attempts": "int"
}

BANK_FIELDS = {
    "customer_id": "id",
    "account_no": "id",
    "balance": "float",
    "txn_type": "string",
    "status": "status"
}

MEDICAL_FIELDS = {
    "patient_id": "id",
    "patient_name": "string",
    "age": "int",
    "gender": "string",
    "diagnosis": "string"
}

# -----------------------------
# DOMAIN DETECTION
# -----------------------------
def detect_domain(prompt):
    p = prompt.lower()

    if any(k in p for k in ["login", "authentication", "auth"]):
        return "login"
    if any(k in p for k in ["bank", "payment", "account"]):
        return "bank"
    if any(k in p for k in ["medical", "patient", "hospital"]):
        return "medical"
    return "generic"

# -----------------------------
# SCHEMA ENGINE (FIXED SYNTAX ERROR HERE)
# -----------------------------
def extract_schema(prompt):

    domain = detect_domain(prompt)

    if domain == "login":
        schema = [{"name": k, "type": v} for k, v in LOGIN_FIELDS.items()]

    elif domain == "bank":
        schema = [{"name": k, "type": v} for k, v in BANK_FIELDS.items()]

    elif domain == "medical":
        # ✅ FIXED SYNTAX ERROR (was } instead of ])
        schema = [{"name": k, "type": v} for k, v in MEDICAL_FIELDS.items()]

    else:

        system = """
Return ONLY JSON schema array.
Fields: name, type
No explanation.
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
            schema = json.loads(raw[start:end])
        except:
            schema = [
                {"name": "id", "type": "id"},
                {"name": "name", "type": "string"}
            ]

    return schema

# -----------------------------
# VALUE ENGINE (NO N/A EVER)
# -----------------------------
def gen_value(field):

    name = field["name"].lower()
    t = field["type"]

    if "id" in name:
        return str(uuid.uuid4())[:10]

    if "email" in name:
        return fake.email()

    if "password" in name:
        return fake.password()

    if "name" in name:
        return fake.name()

    if "phone" in name:
        return "+91" + str(random.randint(6000000000, 9999999999))

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    if t == "status":
        return random.choice(["ACTIVE", "INACTIVE", "PENDING", "BLOCKED"])

    if t == "date":
        return fake.date_this_year().isoformat()

    if "role" in name:
        return random.choice(["ADMIN", "USER", "MANAGER"])

    if "txn" in name:
        return random.choice(["DEBIT", "CREDIT"])

    if "gender" in name:
        return random.choice(["MALE", "FEMALE", "OTHER"])

    return fake.word()

# -----------------------------
# 100K GENERATOR (SAFE)
# -----------------------------
MAX_CHUNK = 5000

def generate_data(schema, rows, prompt):

    data = []
    remaining = rows

    while remaining > 0:

        batch = min(MAX_CHUNK, remaining)

        for _ in range(batch):
            row = {}
            for f in schema:
                row[f["name"]] = gen_value(f)
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
# UI TABS (UNCHANGED)
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

        preview = pd.DataFrame([
            {f["name"]: gen_value(f) for f in schema}
            for _ in range(3)
        ])

        st.dataframe(preview, height=250)

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

        st.markdown("---")
