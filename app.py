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

    if any(k in t for k in ["student", "school", "college", "marks", "class"]):
        return "student"

    if any(k in t for k in ["employee", "hr", "salary", "payroll", "job"]):
        return "hr"

    if any(k in t for k in ["bank", "account", "loan", "transaction"]):
        return "bank"

    if any(k in t for k in ["doctor", "patient", "hospital", "medical"]):
        return "health"

    return "generic"

# -----------------------------
# OPENAI SCHEMA (DOMAIN AWARE)
# -----------------------------
def extract_schema(prompt):

    if STRICT_MODE and not client:
        st.error("❌ API key required")
        st.stop()

    domain = detect_domain(prompt)

    system = f"""
You are a domain-aware enterprise schema generator.

Detected domain: {domain}

Rules:
- Output ONLY JSON array
- Allowed types: id, name, email, phone, address, pincode, status, int, float, date, string

Domain hints:
- student → student_name, roll_number, class, marks, grade
- hr → employee_name, employee_id, department, salary
- bank → account_number, balance, transaction_id
- health → patient_name, disease, doctor_name

Do NOT return empty schema.
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
        st.error("❌ Schema parsing failed")
        st.stop()

# -----------------------------
# VALIDATION (NO BLANK GUARANTEE)
# -----------------------------
def validate_schema(schema):

    allowed = {
        "id","first_name","last_name","full_name",
        "name","student_name","employee_name","patient_name",
        "roll_number","class","marks","grade",
        "email","phone","address","pincode","status",
        "salary","int","float","date","string"
    }

    clean = []
    seen = set()

    for f in schema:

        name = str(f.get("name","")).strip().lower()
        t = str(f.get("type","string")).strip().lower()

        if name not in allowed:
            continue

        if name in seen:
            continue

        seen.add(name)

        clean.append({"name": name, "type": t})

    # 🔥 NEVER ALLOW EMPTY SCHEMA
    if not clean:
        clean = [
            {"name": "name", "type": "name"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"}
        ]

    return clean

# -----------------------------
# CONSISTENT ROW ENGINE
# -----------------------------
def generate(fields, rows):

    data = []

    for _ in range(rows):

        first = fake.first_name()
        last = fake.last_name()
        full = f"{first} {last}"

        email = f"{first.lower()}.{last.lower()}@gmail.com"
        address = fake.address().replace("\n", ", ")
        pincode = random.randint(100000, 999999)

        row = {}

        for f in fields:

            n = f["name"].lower()
            t = f["type"]

            # identity consistency
            if "student_name" in n or "employee_name" in n or "patient_name" in n or "name" in n:
                row[f["name"]] = full

            elif "first" in n:
                row[f["name"]] = first

            elif "last" in n:
                row[f["name"]] = last

            elif "email" in n:
                row[f["name"]] = email

            elif "phone" in n:
                row[f["name"]] = "+91" + str(random.randint(6000000000, 9999999999))

            elif "address" in n:
                row[f["name"]] = address

            elif "pincode" in n:
                row[f["name"]] = pincode

            elif "id" in n or "roll" in n or "account" in n:
                row[f["name"]] = str(uuid.uuid4())[:10]

            elif "marks" in n:
                row[f["name"]] = random.randint(35, 100)

            elif "salary" in n:
                row[f["name"]] = random.randint(20000, 200000)

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
            st.session_state.df.to_excel(buffer, index=False)
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
            {f["name"]: fake.word() for f in fields}
            for _ in range(3)
        ])

        preview.index = range(1, len(preview) + 1)

        st.dataframe(preview)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button("⬇ CSV", preview.to_csv(index=False), f"{item['id']}.csv")

        with col2:
            st.download_button("⬇ JSON", preview.to_json(orient="records"), f"{item['id']}.json")

        with col3:
            buffer = io.BytesIO()
            preview.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("⬇ Excel", buffer, f"{item['id']}.xlsx")

        st.markdown("---")
