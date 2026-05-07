import streamlit as st
import pandas as pd
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime
from openai import OpenAI
import io

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
# OPENAI SCHEMA (CONTROLLED)
# -----------------------------
def extract_schema(prompt):

    system = """
Return ONLY JSON:
[
  {"name": "column_name", "type": "id|name|email|phone|status|int|float|date|text|role|password"}
]
No explanation. No markdown.
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
        return [{"name": "id", "type": "id"},
                {"name": "name", "type": "name"}]

# -----------------------------
# INDUSTRY DETECTION (SAFE)
# -----------------------------
def detect_industry(prompt):
    p = prompt.lower()

    if any(k in p for k in ["bank", "account", "loan", "transaction"]):
        return "bank"
    if any(k in p for k in ["employee", "salary", "hr", "payroll"]):
        return "hr"
    if any(k in p for k in ["insurance", "claim", "policy"]):
        return "insurance"
    if any(k in p for k in ["patient", "hospital", "doctor"]):
        return "healthcare"
    return "generic"

# -----------------------------
# RELATIONAL DATA ENGINE (NEW)
# -----------------------------
def generate_relational(rows):

    employees = []

    for _ in range(rows):
        emp_id = str(uuid.uuid4())[:8]

        employees.append({
            "employee_id": emp_id,
            "name": fake.name(),
            "email": fake.email(),
            "department": random.choice(["IT", "HR", "Finance", "Sales"]),
            "role": random.choice(["ADMIN", "MANAGER", "EXECUTIVE"])
        })

    emp_df = pd.DataFrame(employees)

    payroll = []
    hr = []

    for emp in employees:

        payroll.append({
            "payroll_id": str(uuid.uuid4())[:8],
            "employee_id": emp["employee_id"],
            "salary": round(random.uniform(30000, 250000), 2),
            "bonus": round(random.uniform(1000, 50000), 2),
            "month": fake.month_name()
        })

        hr.append({
            "hr_id": str(uuid.uuid4())[:8],
            "employee_id": emp["employee_id"],
            "manager_name": fake.name(),
            "status": random.choice(["ACTIVE", "INACTIVE", "ONBOARDING"])
        })

    return {
        "employee": emp_df,
        "payroll": pd.DataFrame(payroll),
        "hr": pd.DataFrame(hr)
    }

# -----------------------------
# VALUE ENGINE
# -----------------------------
def gen_value(name, t):

    n = name.lower()

    if "id" in n:
        return str(uuid.uuid4())[:10]

    if "email" in n:
        return fake.email()

    if "phone" in n:
        return "+91" + str(random.randint(6000000000, 9999999999))

    if "status" in n:
        return random.choice(["ACTIVE", "INACTIVE", "BLOCKED", "PENDING"])

    if "role" in n:
        return random.choice(["ADMIN", "USER", "MANAGER"])

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    return fake.word()

# -----------------------------
# GENERATOR
# -----------------------------
def generate(schema, rows):

    data = []

    for _ in range(rows):
        row = {f["name"]: gen_value(f["name"], f["type"]) for f in schema}
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

        if not client:
            st.error("API key required")
            st.stop()

        # -----------------------------
        # RELATIONAL MODE
        # -----------------------------
        if "relational" in prompt.lower():

            tables = generate_relational(rows)
            st.session_state.df = tables

            storage.add({
                "id": str(uuid.uuid4())[:8],
                "name": prompt[:40],
                "schema": "RELATIONAL",
                "created_at": str(datetime.now())
            })

        else:

            schema = extract_schema(prompt)
            df = generate(schema, rows)
            st.session_state.df = df

            storage.add({
                "id": str(uuid.uuid4())[:8],
                "name": prompt[:40],
                "schema": schema,
                "created_at": str(datetime.now())
            })

        st.success("Dataset generated")

    # -----------------------------
    # DISPLAY
    # -----------------------------
    if isinstance(st.session_state.df, dict):

        st.subheader("Employee")
        st.dataframe(st.session_state.df["employee"])

        st.subheader("Payroll")
        st.dataframe(st.session_state.df["payroll"])

        st.subheader("HR")
        st.dataframe(st.session_state.df["hr"])

    elif st.session_state.df is not None:

        st.dataframe(st.session_state.df, height=500)

# =============================
# HISTORY
# =============================
with tab2:

    colA, colB = st.columns([8, 2])

    with colB:
        if st.button("🗑 Delete All History"):
            storage.clear_all()
            st.rerun()

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    for item in reversed(data):

        st.markdown(f"""
        <div style="background:#111827;padding:10px;border-radius:12px;margin-bottom:8px;">
            <h4 style="color:white;margin:0;">📦 {item.get('name')}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
