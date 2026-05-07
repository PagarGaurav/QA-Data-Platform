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

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #6366f1, #3b82f6);
    color: white;
    border-radius: 10px;
}

/* Download buttons */
.stDownloadButton > button {
    background-color: white !important;
    color: black !important;
    font-weight: 600;
    border-radius: 8px;
}

/* Sidebar label fix */
[data-testid="stSidebar"] label {
    color: black !important;
    font-weight: 600;
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
# AI SCHEMA
# -----------------------------
def ai_schema(prompt):

    if not api_key:
        st.error("Enter API key")
        st.stop()

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
Return ONLY JSON:
{
  "name": "...",
  "domain": "...",
  "fields": [
    {"name":"...","type":"string|int|amount|email"}
  ]
}
"""
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(res.choices[0].message.content)


# -----------------------------
# VALUE ENGINE
# -----------------------------
def gen_value(field):

    name = field["name"].lower()
    t = field["type"]

    if "name" in name:
        return fake.name()

    if "email" in name:
        return fake.first_name().lower() + "." + fake.last_name().lower() + "@gmail.com"

    if "vendor" in name:
        return "VEN-" + str(random.randint(10000,99999))

    if "material" in name:
        return "MAT-" + str(random.randint(100000,999999))

    if "po" in name:
        return "PO-" + str(random.randint(100000,999999))

    if t == "int":
        return random.randint(1, 5000)

    if t == "amount":
        return round(random.uniform(10, 10000), 2)

    return fake.word()


# -----------------------------
# VALIDATION + AUTO FIX
# -----------------------------
def is_valid_email(v):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", str(v)))


def auto_fix(field, value):

    name = field["name"].lower()

    if "email" in name:
        if not is_valid_email(value):
            return fake.first_name().lower() + "." + fake.last_name().lower() + "@gmail.com"

    if "vendor" in name:
        return "VEN-" + str(random.randint(10000,99999))

    if "material" in name:
        return "MAT-" + str(random.randint(100000,999999))

    if "po" in name:
        return "PO-" + str(random.randint(100000,999999))

    return value


# -----------------------------
# GENERATOR (ROWS START FROM 1)
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):
        row = {}

        for f in fields:
            val = gen_value(f)
            row[f["name"]] = auto_fix(f, val)

        data.append(row)

    df = pd.DataFrame(data)

    # ROW INDEX START FROM 1
    df.index = range(1, len(df) + 1)

    return df


# -----------------------------
# VERSIONING
# -----------------------------
def create_record(schema, data_store):

    return {
        "id": str(uuid.uuid4())[:8],
        "name": schema.get("name"),
        "domain": schema.get("domain"),
        "version": f"v{len(data_store)+1}",
        "fields": schema.get("fields"),
        "created_at": str(datetime.now())
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

        schema = ai_schema(prompt)

        df = generate(schema["fields"], rows)

        st.session_state.df = df
        st.session_state.record = create_record(schema, storage.get_all())

        storage.add(st.session_state.record)

        st.success(f"{schema['name']} generated")


    if st.session_state.df is not None:

        st.markdown(f"""
        <div style="
            background:#111827;
            padding:12px;
            border-radius:10px;
            margin-bottom:10px;
            font-weight:600;
        ">
        📦 {st.session_state.record["name"]} ({st.session_state.record["version"]})
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

        if st.button("🗑 Delete Last"):
            storage.delete(st.session_state.record["id"])
            st.session_state.df = None
            st.session_state.record = None
            st.rerun()


# =============================
# 📂 HISTORY (REAL DATA PREVIEW)
# =============================
with tab2:

    colA, colB = st.columns([8, 2])

    with colB:
        if st.button("🗑 Delete All History"):
            storage.clear_all()
            st.success("All history deleted")
            st.rerun()

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"### 📦 {item.get('name')} ({item.get('version')})")

        # REAL DATA PREVIEW (NOT SCHEMA)
        sample_fields = item.get("fields", [])

        preview_df = pd.DataFrame([
            {
                f["name"]: gen_value(f)
                for f in sample_fields
            }
            for _ in range(3)
        ])

        # ROWS START FROM 1
        preview_df.index = range(1, len(preview_df) + 1)

        st.dataframe(preview_df)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "⬇ CSV",
                preview_df.to_csv(index=False),
                file_name=f"{item['id']}.csv"
            )

        with col2:
            st.download_button(
                "⬇ JSON",
                json.dumps(item, indent=2),
                file_name=f"{item['id']}.json"
            )

        if st.button("🗑 Delete", key=item["id"]):
            storage.delete(item["id"])
            st.rerun()

        st.markdown("---")
