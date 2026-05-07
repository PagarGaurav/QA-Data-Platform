import streamlit as st
import pandas as pd
import json
import os
import uuid
import io
from datetime import datetime
from openai import OpenAI

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
# CONFIG
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

    def get_all(self):
        return self._read()

storage = Storage(DATA_FILE)

# -----------------------------
# SCHEMA (ONLY STRUCTURE)
# -----------------------------
def extract_schema(prompt):

    system = """
Return ONLY JSON array:
[
  {"name": "column", "type": "name|email|phone|id|address|number|date|text"}
]
No explanation.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    content = res.choices[0].message.content

    start = content.find("[")
    end = content.rfind("]") + 1

    return json.loads(content[start:end])

# -----------------------------
# VALIDATION
# -----------------------------
def validate_schema(schema):

    allowed = {"name","email","phone","id","address","number","date","text"}

    clean = []
    for f in schema:
        clean.append({
            "name": f["name"].strip().lower(),
            "type": f["type"] if f["type"] in allowed else "text"
        })

    return clean

# -----------------------------
# 🚀 PRODUCTION FIELD ENGINE (NO FAKER, NO RANDOM TEXT)
# -----------------------------
def generate_field_value(field_name, field_type, context):

    prompt = f"""
Generate ONE realistic value.

Field: {field_name}
Type: {field_type}
Context: {context}

Rules:
- Must be realistic
- Must match field meaning
- No explanation
- Return ONLY value
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return res.choices[0].message.content.strip()

# -----------------------------
# 🚀 ENTERPRISE DATA GENERATION ENGINE
# -----------------------------
def generate(fields, rows, prompt):

    data = []

    for _ in range(rows):

        row = {}

        # stable identity context
        context = f"Dataset: {prompt}"

        for f in fields:

            name = f["name"]
            t = f["type"]

            # deterministic core fields
            if t == "name":
                row[name] = generate_field_value(name, "name", context)

            elif t == "email":
                row[name] = generate_field_value(name, "email", context)

            elif t == "phone":
                row[name] = generate_field_value(name, "phone", context)

            elif t == "address":
                row[name] = generate_field_value(name, "address", context)

            elif t == "id":
                row[name] = str(uuid.uuid4())

            elif t == "number":
                val = generate_field_value(name, "number", context)
                try:
                    row[name] = int(''.join(filter(str.isdigit, val)))
                except:
                    row[name] = 0

            elif t == "date":
                row[name] = generate_field_value(name, "date", context)

            else:
                row[name] = generate_field_value(name, "text", context)

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
# TABS (UNCHANGED UI)
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])

# =============================
# GENERATE
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        schema = extract_schema(prompt)
        schema = validate_schema(schema)

        df = generate(schema, rows, prompt)

        st.session_state.df = df

        storage.add({
            "id": str(uuid.uuid4())[:8],
            "name": prompt[:40],
            "fields": schema,
            "created_at": str(datetime.now())
        })

        st.success("Dataset generated successfully")

    if st.session_state.df is not None:

        st.dataframe(st.session_state.df)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button("CSV", st.session_state.df.to_csv(index=False), "data.csv")

        with col2:
            st.download_button("JSON", st.session_state.df.to_json(orient="records"), "data.json")

        with col3:
            buffer = io.BytesIO()
            st.session_state.df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("Excel", buffer, "data.xlsx")

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
        <div style="background:#111827;padding:12px;border-radius:12px;margin-bottom:10px;">
            <h4 style="color:white;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
