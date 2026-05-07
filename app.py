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
# UI (NO CHANGE)
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
STRICT_MODE = True

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
# DOMAIN DETECTION
# -----------------------------
def detect_domain(text):
    t = text.lower()

    if "student" in t or "school" in t or "college" in t:
        return "student"

    return "generic"

# -----------------------------
# OPENAI SCHEMA
# -----------------------------
def extract_schema(prompt):

    if STRICT_MODE and not client:
        st.error("❌ API key required")
        st.stop()

    domain = detect_domain(prompt)

    system = f"""
You are a STRICT enterprise schema generator.

Detected domain: {domain}

Rules:
- Output ONLY JSON array
- Allowed types: id, name, email, phone, address, pincode, status, int, float, date, string
- For student domain include: student_name, roll_no, std, email, phone
- Never return empty schema
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
        st.error("❌ Schema parse failed")
        st.stop()

# -----------------------------
# VALIDATION (NO DATA LOSS)
# -----------------------------
def validate_schema(schema):

    allowed = {
        "id","student_name","first_name","last_name","full_name",
        "email","phone","address","pincode","status",
        "roll_no","std",
        "int","float","date","string"
    }

    clean = []
    seen = set()

    for f in schema:
        name = f.get("name","").lower()

        if name not in allowed:
            continue

        if name in seen:
            continue

        seen.add(name)
        clean.append(f)

    return clean

# -----------------------------
# STUDENT GUARANTEE LAYER (KEY FIX)
# -----------------------------
def enforce_student_schema(fields, prompt):

    if "student" in prompt.lower():

        required = [
            {"name": "student_name", "type": "name"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "roll_no", "type": "id"},
            {"name": "std", "type": "string"}
        ]

        existing = {f["name"] for f in fields}

        for r in required:
            if r["name"] not in existing:
                fields.append(r)

    return fields

# -----------------------------
# GENERATION ENGINE (CONSISTENT)
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):

        first = fake.first_name()
        last = fake.last_name()
        full = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}@gmail.com"

        row = {}

        for f in fields:

            n = f["name"].lower()
            t = f["type"]

            if "student_name" in n or "name" in n:
                row[f["name"]] = full

            elif "email" in n:
                row[f["name"]] = email

            elif "phone" in n:
                row[f["name"]] = "+91" + str(random.randint(6000000000, 9999999999))

            elif "roll_no" in n:
                row[f["name"]] = random.randint(1000, 99999)

            elif "std" in n:
                row[f["name"]] = random.choice(["1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th","11th","12th"])

            elif "address" in n:
                row[f["name"]] = fake.address().replace("\n", ", ")

            elif "pincode" in n:
                row[f["name"]] = random.randint(100000, 999999)

            elif "id" in n:
                row[f["name"]] = str(uuid.uuid4())[:10]

            elif "status" in n:
                row[f["name"]] = random.choice(["ACTIVE","INACTIVE","PENDING","BLOCKED"])

            elif t == "int":
                row[f["name"]] = random.randint(1, 9999)

            elif t == "float":
                row[f["name"]] = round(random.uniform(100, 100000), 2)

            elif t == "date":
                row[f["name"]] = fake.date_this_year().isoformat()

            else:
                row[f["name"]] = fake.word()

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

        fields = extract_schema(prompt)
        fields = validate_schema(fields)
        fields = enforce_student_schema(fields, prompt)

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
            st.session_state.df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("⬇ Excel", buffer, "data.xlsx")

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
