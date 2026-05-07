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
# SAFE VALUE ENGINE (SAME LOGIC)
# -----------------------------
def gen_value(name):

    n = name.lower()

    if "id" in n:
        return str(uuid.uuid4())[:10]

    if "name" in n:
        return fake.name()

    if "email" in n:
        return f"{fake.user_name()}@gmail.com"

    if "phone" in n:
        return "+91" + str(random.randint(6000000000, 9999999999))

    if "status" in n:
        return random.choice(["ACTIVE","INACTIVE","PENDING","BLOCKED"])

    return fake.word()

# -----------------------------
# SIMPLE SCHEMA
# -----------------------------
def smart_schema(prompt):

    text = prompt.lower()

    fields = [{"name": "id"}]

    fields += [
        {"name": "name"},
        {"name": "email"},
        {"name": "phone"},
        {"name": "status"}
    ]

    return fields

# -----------------------------
# GENERATOR (✔ INDEX FIX HERE)
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):
        row = {f["name"]: gen_value(f["name"]) for f in fields}
        data.append(row)

    df = pd.DataFrame(data)

    # ✅ FIX: index starts from 1
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

        fields = smart_schema(prompt)
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
# HISTORY (✔ DELETE PER GRID FIXED)
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
            {f["name"]: gen_value(f["name"]) for f in fields}
            for _ in range(3)
        ])

        # optional display index (already safe now)
        preview.index = range(1, len(preview) + 1)

        st.dataframe(preview)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.download_button("⬇ CSV", preview.to_csv(index=False), f"{item['id']}.csv")

        with col2:
            st.download_button("⬇ JSON", preview.to_json(orient="records"), f"{item['id']}.json")

        with col3:
            buffer = io.BytesIO()
            preview.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button("⬇ Excel", buffer, f"{item['id']}.xlsx")

        # ✅ FIX: DELETE PER GRID (correct key + working rerun)
        with col4:
            if st.button("🗑 Delete", key=item["id"]):
                storage.delete(item["id"])
                st.rerun()

        st.markdown("---")
