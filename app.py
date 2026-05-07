import streamlit as st
import pandas as pd
import random
import json
import os
import uuid
from datetime import datetime
import io
from faker import Faker
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
# SCHEMA EXTRACTION (LLM ONLY)
# -----------------------------
def extract_schema(prompt):

    if not client:
        st.error("API key required")
        st.stop()

    system = """
Return ONLY JSON array:
[
  {"name": "column", "type": "name|email|phone|id|address|number|date|text"}
]
No explanation. No extra text.
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

    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        return json.loads(content[start:end])
    except:
        st.error("Schema parsing failed")
        st.stop()

# -----------------------------
# VALIDATION
# -----------------------------
def validate_schema(schema):

    allowed = {"name","email","phone","id","address","number","date","text"}

    clean = []

    for f in schema:
        name = f.get("name","col").strip().lower()
        t = f.get("type","text").strip().lower()

        if t not in allowed:
            t = "text"

        clean.append({"name": name, "type": t})

    return clean

# -----------------------------
# TEXT INTELLIGENCE ENGINE (FIXES GARBAGE OUTPUT)
# -----------------------------
def smart_text(field, person):

    f = field.lower()
    first = person.split()[0]

    if "role" in f or "job" in f:
        return random.choice([
            "Software Engineer",
            "Data Analyst",
            "Project Manager",
            "Business Analyst",
            "Consultant"
        ])

    if "company" in f:
        return random.choice([
            "Google", "Microsoft", "Amazon", "TCS", "Infosys"
        ])

    if "status" in f:
        return random.choice(["Active", "Inactive", "Pending", "Completed"])

    if "feedback" in f:
        return random.choice([
            "Good experience",
            "Very satisfied",
            "Needs improvement",
            "Excellent service",
            "Average experience"
        ])

    if "description" in f:
        return f"{first} is a professional with relevant domain experience."

    return f"Valid {field} for {first}"

# -----------------------------
# ENTERPRISE DATA ENGINE
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):

        row = {}

        person = fake.name()
        first = person.split()[0].lower()

        for f in fields:

            name = f["name"]
            t = f["type"]

            if t == "name":
                row[name] = person

            elif t == "email":
                row[name] = f"{first}{random.randint(10,999)}@gmail.com"

            elif t == "phone":
                row[name] = f"+91-{random.randint(70000,99999)}-{random.randint(10000,99999)}"

            elif t == "address":
                row[name] = f"{fake.city()}, {fake.country()}"

            elif t == "id":
                row[name] = str(uuid.uuid4())

            elif t == "number":
                row[name] = random.randint(1, 10000)

            elif t == "date":
                row[name] = fake.date_between("-3y", "today").isoformat()

            else:
                row[name] = smart_text(name, person)

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
# TABS (UNCHANGED)
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])

# =============================
# GENERATE
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        st.session_state["last_prompt"] = prompt

        schema = extract_schema(prompt)
        schema = validate_schema(schema)

        df = generate(schema, rows)
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

        fields = item.get("fields", [])

        preview = pd.DataFrame([
            {f["name"]: fake.word() for f in fields}
            for _ in range(3)
        ])

        preview.index = range(1, len(preview) + 1)

        st.dataframe(preview)

        st.markdown("---")
