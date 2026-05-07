import streamlit as st
import pandas as pd
import json
import os
import uuid
import io
import random
from datetime import datetime
from faker import Faker
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

    def delete(self, item_id):
        data = self._read()
        data = [x for x in data if x["id"] != item_id]
        self._write(data)

    def clear_all(self):
        self._write([])

storage = Storage(DATA_FILE)

# -----------------------------
# SCHEMA EXTRACTION (FAST)
# -----------------------------
def extract_schema(prompt):

    system = """
Return ONLY JSON array:
[
  {"name": "column"}
]
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
# 🧠 SEMANTIC COLUMN MAPPER (CRITICAL FIX)
# -----------------------------
def semantic_map_schema(schema, prompt):

    system = """
You map dataset columns to correct semantic types.

Return ONLY JSON array:
[
 {"name":"col","type":"name|email|phone|id|address|number|date|role|status|text"}
]

Rules:
- Understand meaning (designation = role, residence = address, etc.)
- No keyword matching only
- Be logically correct
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"""
Prompt: {prompt}
Columns: {json.dumps(schema)}
"""}
        ],
        temperature=0
    )

    content = res.choices[0].message.content

    start = content.find("[")
    end = content.rfind("]") + 1

    return json.loads(content[start:end])

# -----------------------------
# 🚀 FAST DATA ENGINE (NO GPT ROWS)
# -----------------------------
def generate(fields, rows, prompt):

    data = []

    for _ in range(rows):

        row = {}

        person = fake.name()
        first = person.split()[0].lower()
        email = f"{first}{random.randint(10,999)}@gmail.com"
        phone = f"+91-{random.randint(70000,99999)}-{random.randint(10000,99999)}"

        for f in fields:

            name = f["name"]
            t = f["type"]

            if t == "name":
                row[name] = person

            elif t == "email":
                row[name] = email

            elif t == "phone":
                row[name] = phone

            elif t == "address":
                row[name] = f"{fake.city()}, {fake.country()}"

            elif t == "id":
                row[name] = str(uuid.uuid4())[:12]

            elif t == "number":
                row[name] = random.randint(1, 10000)

            elif t == "date":
                row[name] = fake.date_between("-3y", "today").isoformat()

            elif t == "role":
                row[name] = random.choice([
                    "Software Engineer",
                    "Data Analyst",
                    "Product Manager",
                    "Consultant",
                    "HR Executive"
                ])

            elif t == "status":
                row[name] = random.choice([
                    "Active", "Inactive", "Pending", "Completed"
                ])

            else:
                row[name] = fake.word()

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

        # 🔥 FIX APPLIED HERE (IMPORTANT)
        schema = semantic_map_schema(schema, prompt)

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
# HISTORY (UNCHANGED UI)
# =============================
with tab2:

    data = storage.get_all()

    col1, col2 = st.columns([8,2])

    with col2:
        if st.button("🗑 Delete All"):
            storage.clear_all()
            st.rerun()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"""
        <div style="background:#111827;padding:12px;border-radius:12px;margin-bottom:10px;">
            <h4 style="color:white;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        df = pd.DataFrame(item.get("fields", []))

        st.dataframe(df)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.download_button("CSV", df.to_csv(index=False), file_name=f"{item['id']}.csv")

        with c2:
            st.download_button("JSON", df.to_json(orient="records"), file_name=f"{item['id']}.json")

        with c3:
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("Excel", buffer, file_name=f"{item['id']}.xlsx")

        with c4:
            if st.button(f"🗑 Delete {item['id']}", key=item["id"]):
                storage.delete(item["id"])
                st.rerun()

        st.markdown("---")
