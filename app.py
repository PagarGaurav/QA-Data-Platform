import streamlit as st
import pandas as pd
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime
import io
from openai import OpenAI

fake = Faker()

# -----------------------------
# UI (DO NOT CHANGE)
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
# STRICT MODE CONFIG
# -----------------------------
STRICT_MODE = True

# -----------------------------
# API KEY (REQUIRED IN STRICT MODE)
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
# STRICT EMAIL
# -----------------------------
def safe_email():
    return f"{fake.user_name()}@gmail.com"

# -----------------------------
# OPENAI SCHEMA (STRICT CONTRACT)
# -----------------------------
def extract_schema(prompt):

    if STRICT_MODE and not client:
        st.error("❌ STRICT MODE: API key required")
        st.stop()

    system = """
You are a STRICT DATA SCHEMA ENGINE.

Return ONLY JSON array:
[
  {"name": "column_name", "type": "id|name|email|phone|status|int|float|date|role|string"}
]

RULES:
- no explanation
- no extra text
- no duplicate columns
- only valid schema fields
- snake_case names only
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    content = res.choices[0].message.content

    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        return json.loads(content[start:end])
    except:
        st.error("❌ Invalid schema from OpenAI")
        st.stop()

# -----------------------------
# SCHEMA VALIDATION (ENTERPRISE)
# -----------------------------
def validate_schema(schema):

    allowed = {
        "id","name","email","phone","status",
        "int","float","date","role","string"
    }

    cleaned = []
    seen = set()

    for f in schema:

        name = str(f.get("name","")).strip().lower()
        t = str(f.get("type","string")).strip().lower()

        if not name:
            continue

        if name in seen:
            continue
        seen.add(name)

        if t not in allowed:
            t = "string"

        cleaned.append({"name": name, "type": t})

    if not cleaned:
        st.error("❌ Schema empty after validation")
        st.stop()

    return cleaned

# -----------------------------
# VALUE ENGINE (NO GARBAGE)
# -----------------------------
def gen_value(name, t):

    n = name.lower()

    if "id" in n:
        return str(uuid.uuid4())[:10]

    if "name" in n:
        return fake.first_name() + " " + fake.last_name()

    if "email" in n:
        return safe_email()

    if "phone" in n:
        return "+91" + str(random.randint(6000000000, 9999999999))

    if "status" in n:
        return random.choice(["ACTIVE","INACTIVE","PENDING","BLOCKED"])

    if "role" in n:
        return random.choice(["ADMIN","USER","MANAGER"])

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    if t == "date":
        return fake.date_this_year().isoformat()

    if t == "string":
        return fake.word()

    return "UNKNOWN"

# -----------------------------
# GENERATOR (STRICT COLUMNS ONLY)
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):
        row = {}

        for f in fields:
            row[f["name"]] = gen_value(f["name"], f["type"])

        data.append(row)

    return pd.DataFrame(data)

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

        if STRICT_MODE and not client:
            st.error("❌ STRICT MODE: API key required")
            st.stop()

        fields = extract_schema(prompt)
        fields = validate_schema(fields)

        df = generate(fields, rows)
        st.session_state.df = df

        storage.add({
            "id": str(uuid.uuid4())[:8],
            "name": prompt[:40],
            "fields": fields,
            "created_at": str(datetime.now())
        })

        st.success("Dataset generated")

    if st.session_state.df is not None:

        st.dataframe(st.session_state.df)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button("⬇ CSV", st.session_state.df.to_csv(index=False), "data.csv")

        with col2:
            st.download_button("⬇ JSON", st.session_state.df.to_json(orient="records"), "data.json")

        with col3:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                st.session_state.df.to_excel(writer, index=False)
            buffer.seek(0)

            st.download_button("⬇ Excel", buffer, "data.xlsx")

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
        <div style="background:#111827;padding:12px;border-radius:12px;margin-bottom:10px;">
            <h4 style="color:white;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        fields = item.get("fields", [])

        preview = pd.DataFrame([
            {f["name"]: gen_value(f["name"], f["type"]) for f in fields}
            for _ in range(3)
        ])

        st.dataframe(preview)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button("⬇ CSV", preview.to_csv(index=False), f"{item['id']}.csv")

        with col2:
            st.download_button("⬇ JSON", preview.to_json(orient="records"), f"{item['id']}.json")

        with col3:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                preview.to_excel(writer, index=False)
            buffer.seek(0)

            st.download_button("⬇ Excel", buffer, f"{item['id']}.xlsx")

        st.markdown("---")
