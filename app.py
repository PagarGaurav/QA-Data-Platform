import streamlit as st
import pandas as pd
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime
from openai import OpenAI
import io
import re

fake = Faker()

# -----------------------------
# UI (UNCHANGED - DO NOT TOUCH)
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
# OPENAI
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
# OPENAI SCHEMA EXTRACTION (CONTROLLED)
# -----------------------------
def extract_schema(prompt):

    system = """
Return ONLY valid JSON array:

[
  {"name": "column", "type": "id|name|email|phone|status|int|float|date|role|text|password"}
]

Rules:
- no explanation
- no markdown
- clean structured output only
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    content = res.choices[0].message.content.strip()

    # clean markdown if any
    content = re.sub(r"```json|```", "", content)

    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        return json.loads(content[start:end])
    except:
        return [{"name": "id", "type": "id"},
                {"name": "name", "type": "name"}]

# -----------------------------
# VALIDATION LAYER (IMPORTANT FIX)
# -----------------------------
def validate_schema(schema):

    clean = []

    for f in schema:
        name = str(f.get("name", "")).strip().lower()
        t = str(f.get("type", "text")).strip().lower()

        if not name:
            continue

        allowed = {
            "id","name","email","phone","status","int",
            "float","date","role","text","password"
        }

        if t not in allowed:
            t = "text"

        clean.append({"name": name, "type": t})

    return clean

# -----------------------------
# VALUE ENGINE (ACCURATE + DOMAIN SAFE)
# -----------------------------
def gen_value(name, t):

    n = name.lower()

    # ID
    if "id" in n:
        return str(uuid.uuid4())[:10]

    # EMAIL
    if "email" in n:
        return fake.email()

    # PHONE
    if "phone" in n or "mobile" in n:
        return "+91" + str(random.randint(6000000000, 9999999999))

    # STATUS
    if "status" in n:
        return random.choice(["ACTIVE","INACTIVE","BLOCKED","PENDING"])

    # ROLE
    if "role" in n:
        return random.choice(["ADMIN","USER","MANAGER","EXECUTIVE"])

    # BANKING LOGIC
    if "txn" in n or "transaction" in n:
        return random.choice(["DEBIT","CREDIT"])

    if "balance" in n or "amount" in n:
        return round(random.uniform(100, 500000), 2)

    if "account" in n:
        return str(random.randint(1000000000, 9999999999))

    # HR LOGIC
    if "salary" in n:
        return round(random.uniform(20000, 300000), 2)

    if "employee" in n or "name" in n:
        return fake.name()

    # HEALTHCARE
    if "diagnosis" in n:
        return random.choice([
            "Diabetes","Hypertension","Asthma","Flu","Migraine","Infection"
        ])

    if "age" in n:
        return random.randint(1, 90)

    # TYPE BASED
    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    if t == "date":
        return fake.date_this_year().isoformat()

    return fake.word()

# -----------------------------
# GENERATOR
# -----------------------------
def generate(schema, rows):

    data = []

    for _ in range(rows):
        row = {}
        for f in schema:
            row[f["name"]] = gen_value(f["name"], f["type"])
        data.append(row)

    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)

    return df

# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

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
            st.error("API Key required")
            st.stop()

        schema = extract_schema(prompt)
        schema = validate_schema(schema)

        df = generate(schema, rows)

        st.session_state.df = df

        storage.add({
            "id": str(uuid.uuid4())[:8],
            "name": prompt[:40],
            "schema": schema,
            "created_at": str(datetime.now())
        })

        st.success("Dataset generated")

    if st.session_state.df is not None:

        st.dataframe(st.session_state.df, height=500)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                st.session_state.df.to_csv(index=False),
                file_name="data.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                st.session_state.df.to_json(orient="records"),
                file_name="data.json"
            )

# =============================
# HISTORY (UNCHANGED UI)
# =============================
with tab2:

    colA, colB = st.columns([8, 2])

    with colB:
        if st.button("🗑 Delete All History"):
            storage.clear_all()
            st.rerun()

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"""
        <div style="background:#111827;padding:10px;border-radius:12px;margin-bottom:8px;">
            <h4 style="color:white;margin:0;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        schema = item.get("schema", [])

        preview = pd.DataFrame([
            {f["name"]: gen_value(f["name"], f["type"]) for f in schema}
            for _ in range(3)
        ]).fillna("")

        st.dataframe(preview, height=200)

        col1, col2, col3 = st.columns(3)

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

        with col3:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                preview.to_excel(writer, index=False, sheet_name="data")
            buffer.seek(0)

            st.download_button(
                "⬇ Excel",
                buffer,
                file_name=f"{item['id']}.xlsx"
            )

        st.markdown("---")
