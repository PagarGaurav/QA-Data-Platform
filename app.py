import streamlit as st
import pandas as pd
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

    def clear_all(self):
        self._write([])

    def get_all(self):
        return self._read()

storage = Storage(DATA_FILE)

# -----------------------------
# DOMAIN DETECTION (SAFE)
# -----------------------------
def detect_domain(prompt):
    p = prompt.lower()

    if "login" in p or "auth" in p:
        return "login"
    if "bank" in p:
        return "bank"
    if "medical" in p:
        return "medical"
    return "generic"

# -----------------------------
# OPENAI SCHEMA NORMALIZATION (ONLY PLACE OPENAI USED)
# -----------------------------
def get_schema_from_openai(prompt):

    system = """
You are a data architect.

Convert user request into structured dataset schema.

Return ONLY JSON array:

[
  {"name": "column_name", "type": "one_of: id, email, phone, name, int, float, status, date, text, role, password"}
]

Rules:
- no explanation
- no extra text
- clean column names only
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
        schema = [{"name": "id", "type": "id"},
                  {"name": "name", "type": "name"}]

    return schema

# -----------------------------
# VALUE ENGINE (STRICT + CORRECT)
# -----------------------------
def gen_value(t):

    if t == "id":
        return str(uuid.uuid4())[:10]

    if t == "email":
        return fake.email()

    if t == "phone":
        return "+91" + str(random.randint(6000000000, 9999999999))

    if t == "name":
        return fake.name()

    if t == "password":
        return fake.password(length=10, special_chars=False)

    if t == "role":
        return random.choice(["ADMIN", "USER", "MANAGER"])

    if t == "status":
        return random.choice(["ACTIVE", "INACTIVE", "BLOCKED", "PENDING"])

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    if t == "date":
        return fake.date_this_year().isoformat()

    if t == "text":
        return fake.word()

    return fake.word()

# -----------------------------
# GENERATOR
# -----------------------------
def generate(schema, rows):

    data = []

    for _ in range(rows):
        row = {}
        for f in schema:
            row[f["name"]] = gen_value(f["type"])
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
# UI TABS (UNCHANGED)
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])

with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        if not client:
            st.error("Please add OpenAI API key")
            st.stop()

        schema = get_schema_from_openai(prompt)
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

with tab2:

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"""
        <div style="background:#111827;padding:12px;border-radius:12px;margin-bottom:10px;">
            <h4 style="color:white;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        schema = item.get("schema", [])

        preview = pd.DataFrame([
            {f["name"]: gen_value(f["type"]) for f in schema}
            for _ in range(3)
        ])

        st.dataframe(preview, height=250)

        st.markdown("---")
