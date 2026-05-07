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

# =========================================================
# UI (UNCHANGED)
# =========================================================
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

# =========================================================
# CONFIG
# =========================================================
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

# =========================================================
# MODE SELECTOR
# =========================================================
mode = st.sidebar.selectbox(
    "🧠 Generation Mode",
    [
        "Auto Detect",
        "HR",
        "CRM",
        "Banking",
        "Analytics",
        "QA Testing",
        "Generic"
    ]
)

# =========================================================
# STORAGE
# =========================================================
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

# =========================================================
# HELPERS
# =========================================================
def valid_phone():
    return "+91" + random.choice(["6", "7", "8", "9"]) + "".join(
        [str(random.randint(0, 9)) for _ in range(9)]
    )

def valid_email(name):
    first = name.split()[0].lower()
    return f"{first}{random.randint(100,999)}@gmail.com"

def random_date():
    return fake.date_between("-3y", "today").isoformat()

def detect_mode(prompt):

    p = prompt.lower()

    rules = {
        "HR": ["employee", "salary", "designation", "department"],
        "CRM": ["lead", "sales", "customer", "deal"],
        "Banking": ["bank", "loan", "kyc", "account"],
        "Analytics": ["kpi", "analytics", "dashboard"],
    }

    for mode_name, keywords in rules.items():
        if any(k in p for k in keywords):
            return mode_name

    return "Generic"

# =========================================================
# BULLETPROOF SCHEMA EXTRACTION
# =========================================================
def extract_schema(prompt):

    if not client:
        st.error("API key required")
        st.stop()

    system = """
Return ONLY JSON array.

Example:
[
  {"name":"employee_name"},
  {"name":"salary"}
]

Rules:
- Every item MUST contain "name"
- No extra text
"""

    try:

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":prompt}
            ],
            temperature=0.1
        )

        content = res.choices[0].message.content

        start = content.find("[")
        end = content.rfind("]") + 1

        raw = json.loads(content[start:end])

        cleaned = []

        for item in raw:

            # STRING
            if isinstance(item, str):

                cleaned.append({
                    "name": item.strip().lower().replace(" ", "_")
                })

            # DICT
            elif isinstance(item, dict):

                if "name" in item:
                    val = item["name"]

                elif "column" in item:
                    val = item["column"]

                elif "field" in item:
                    val = item["field"]

                else:
                    val = "unknown_column"

                cleaned.append({
                    "name": str(val).strip().lower().replace(" ", "_")
                })

        if not cleaned:

            cleaned = [
                {"name":"name"},
                {"name":"email"},
                {"name":"phone"}
            ]

        return cleaned

    except Exception:

        return [
            {"name":"name"},
            {"name":"email"},
            {"name":"phone"}
        ]

# =========================================================
# HR MODE
# =========================================================
def generate_hr(fields, rows):

    roles = {
        "Software Engineer": (60000, 180000),
        "Data Analyst": (50000, 120000),
        "Manager": (100000, 250000),
        "HR Executive": (40000, 90000)
    }

    departments = [
        "Engineering",
        "Finance",
        "HR",
        "Operations",
        "Product"
    ]

    data = []

    for _ in range(rows):

        row = {}

        name = fake.name()
        role = random.choice(list(roles.keys()))
        salary = random.randint(*roles[role])

        for f in fields:

            col = str(f.get("name", "unknown")).lower()

            if "name" in col:
                row[col] = name

            elif "email" in col:
                row[col] = valid_email(name)

            elif "phone" in col or "mobile" in col:
                row[col] = valid_phone()

            elif "salary" in col:
                row[col] = salary

            elif "designation" in col or "role" in col:
                row[col] = role

            elif "department" in col:
                row[col] = random.choice(departments)

            elif "age" in col:
                row[col] = random.randint(22, 60)

            elif "date" in col:
                row[col] = random_date()

            else:
                row[col] = fake.word()

        data.append(row)

    return pd.DataFrame(data)

# =========================================================
# CRM MODE
# =========================================================
def generate_crm(fields, rows):

    statuses = ["New", "Qualified", "Won", "Lost"]

    data = []

    for _ in range(rows):

        row = {}

        name = fake.name()

        for f in fields:

            col = str(f.get("name", "unknown")).lower()

            if "name" in col:
                row[col] = name

            elif "email" in col:
                row[col] = valid_email(name)

            elif "phone" in col or "mobile" in col:
                row[col] = valid_phone()

            elif "status" in col:
                row[col] = random.choice(statuses)

            elif "deal" in col or "amount" in col:
                row[col] = random.randint(10000, 500000)

            elif "date" in col:
                row[col] = random_date()

            else:
                row[col] = fake.word()

        data.append(row)

    return pd.DataFrame(data)

# =========================================================
# BANKING MODE
# =========================================================
def generate_banking(fields, rows):

    account_types = ["Savings", "Current", "Business"]

    data = []

    for _ in range(rows):

        row = {}

        name = fake.name()

        for f in fields:

            col = str(f.get("name", "unknown")).lower()

            if "name" in col:
                row[col] = name

            elif "email" in col:
                row[col] = valid_email(name)

            elif "phone" in col or "mobile" in col:
                row[col] = valid_phone()

            elif "account" in col:
                row[col] = random.randint(1000000000, 9999999999)

            elif "balance" in col:
                row[col] = random.randint(5000, 5000000)

            elif "kyc" in col:
                row[col] = random.choice(["Verified", "Pending"])

            elif "type" in col:
                row[col] = random.choice(account_types)

            elif "date" in col:
                row[col] = random_date()

            else:
                row[col] = fake.word()

        data.append(row)

    return pd.DataFrame(data)

# =========================================================
# ANALYTICS MODE
# =========================================================
def generate_analytics(fields, rows):

    data = []
    base = 100

    for _ in range(rows):

        row = {}

        for f in fields:

            col = str(f.get("name", "unknown")).lower()

            if "date" in col:
                row[col] = random_date()

            elif "sales" in col or "revenue" in col:
                base += random.randint(-10, 30)
                row[col] = base

            else:
                row[col] = random.randint(1, 100)

        data.append(row)

    return pd.DataFrame(data)

# =========================================================
# QA MODE
# =========================================================
def generate_qa(fields, rows):

    data = []

    for i in range(rows):

        row = {}

        for f in fields:

            col = str(f.get("name", "unknown")).lower()

            if i % 5 == 0:
                row[col] = None

            elif i % 7 == 0:
                row[col] = "INVALID_DATA"

            else:
                row[col] = fake.word()

        data.append(row)

    return pd.DataFrame(data)

# =========================================================
# GENERIC MODE
# =========================================================
def generate_generic(fields, rows):

    data = []

    for _ in range(rows):

        row = {}

        name = fake.name()

        for f in fields:

            col = str(f.get("name", "unknown")).lower()

            if "name" in col:
                row[col] = name

            elif "email" in col:
                row[col] = valid_email(name)

            elif "phone" in col or "mobile" in col:
                row[col] = valid_phone()

            elif "city" in col:
                row[col] = fake.city()

            elif "address" in col:
                row[col] = fake.address().replace("\n", ", ")

            elif "date" in col:
                row[col] = random_date()

            elif "id" in col:
                row[col] = str(uuid.uuid4())[:10]

            elif "amount" in col or "price" in col:
                row[col] = random.randint(1000, 500000)

            elif "age" in col:
                row[col] = random.randint(18, 65)

            else:
                row[col] = fake.word()

        data.append(row)

    return pd.DataFrame(data)

# =========================================================
# ROUTER
# =========================================================
def generate_dataset(mode, fields, rows, prompt):

    if mode == "Auto Detect":
        mode = detect_mode(prompt)

    generators = {
        "HR": generate_hr,
        "CRM": generate_crm,
        "Banking": generate_banking,
        "Analytics": generate_analytics,
        "QA Testing": generate_qa,
        "Generic": generate_generic
    }

    fn = generators.get(mode, generate_generic)

    return fn(fields, rows)

# =========================================================
# REPAIR
# =========================================================
def repair_dataframe(df):

    for col in df.columns:
        df[col] = df[col].fillna("N/A")

    return df

# =========================================================
# SESSION
# =========================================================
if "df" not in st.session_state:
    st.session_state.df = None

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])

# =========================================================
# GENERATE
# =========================================================
with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        schema = extract_schema(prompt)

        df = generate_dataset(
            mode,
            schema,
            rows,
            prompt
        )

        df = repair_dataframe(df)

        df.index = range(1, len(df) + 1)

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
            st.download_button(
                "CSV",
                st.session_state.df.to_csv(index=False),
                "data.csv"
            )

        with col2:
            st.download_button(
                "JSON",
                st.session_state.df.to_json(orient="records"),
                "data.json"
            )

        with col3:
            buffer = io.BytesIO()

            st.session_state.df.to_excel(
                buffer,
                index=False
            )

            buffer.seek(0)

            st.download_button(
                "Excel",
                buffer,
                "data.xlsx"
            )

# =========================================================
# HISTORY
# =========================================================
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

        fields = item.get("fields", [])

        preview = pd.DataFrame([
            {str(f.get("name", "unknown")): fake.word() for f in fields}
            for _ in range(3)
        ])

        preview.index = range(1, len(preview) + 1)

        st.dataframe(preview)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.download_button(
                "CSV",
                preview.to_csv(index=False),
                file_name=f"{item['id']}.csv"
            )

        with c2:
            st.download_button(
                "JSON",
                preview.to_json(orient="records"),
                file_name=f"{item['id']}.json"
            )

        with c3:
            buffer = io.BytesIO()

            preview.to_excel(
                buffer,
                index=False
            )

            buffer.seek(0)

            st.download_button(
                "Excel",
                buffer,
                file_name=f"{item['id']}.xlsx"
            )

        with c4:
            if st.button(
                f"🗑 Delete {item['id']}",
                key=item["id"]
            ):
                storage.delete(item["id"])
                st.rerun()

        st.markdown("---")
