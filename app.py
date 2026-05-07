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
import re

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
# SAFE EMAIL (VALID ALWAYS)
# -----------------------------
def safe_email():
    return f"{fake.user_name()}@gmail.com"

# -----------------------------
# STRICT NAME HANDLING (FIXED ROOT CAUSE)
# -----------------------------
def generate_name(field):

    n = field.lower()

    # explicit split support
    if "first" in n:
        return fake.first_name()

    if "last" in n:
        return fake.last_name()

    if "full" in n or n == "name":
        return fake.first_name() + " " + fake.last_name()

    # fallback safe full name
    return fake.first_name() + " " + fake.last_name()

# -----------------------------
# SCHEMA FROM OPENAI
# -----------------------------
def extract_schema(prompt):

    system = """
Return ONLY JSON array:

[
  {"name": "column", "type": "id|name|email|phone|status|int|float|date|role"}
]

No explanation.
No extra text.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    content = res.choices[0].message.content.strip()
    content = re.sub(r"```json|```", "", content)

    try:
        start = content.index("[")
        end = content.rindex("]") + 1
        return json.loads(content[start:end])
    except:
        return [{"name": "id", "type": "id"},
                {"name": "name", "type": "name"}]

# -----------------------------
# VALIDATION (REMOVE BAD SCHEMA)
# -----------------------------
def validate_schema(schema):

    allowed = {
        "id","name","email","phone","status",
        "int","float","date","role"
    }

    clean = []

    for f in schema:
        name = str(f.get("name","")).strip().lower()
        t = str(f.get("type","text")).strip().lower()

        if not name:
            continue

        if t not in allowed:
            t = "text"

        clean.append({"name": name, "type": t})

    return clean

# -----------------------------
# VALUE ENGINE (SINGLE SOURCE OF TRUTH)
# -----------------------------
def gen_value(name, t):

    n = name.lower()

    if "id" in n:
        return str(uuid.uuid4())[:10]

    if "email" in n:
        return safe_email()

    if "phone" in n:
        return "+91" + str(random.randint(6000000000, 9999999999))

    if "status" in n:
        return random.choice(["ACTIVE","INACTIVE","BLOCKED","PENDING"])

    if "role" in n:
        return random.choice(["ADMIN","USER","MANAGER"])

    if "txn" in n:
        return random.choice(["DEBIT","CREDIT"])

    if "balance" in n or "amount" in n:
        return round(random.uniform(100, 500000), 2)

    if "salary" in n:
        return round(random.uniform(20000, 300000), 2)

    if "diagnosis" in n:
        return random.choice(["Diabetes","Asthma","Flu","Infection"])

    if "age" in n:
        return random.randint(1, 90)

    # ✅ FIXED NAME LOGIC (NO MORE BUGS)
    if "name" in n:
        return generate_name(n)

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    if t == "date":
        return fake.date_this_year().isoformat()

    return "N/A"

# -----------------------------
# GENERATOR
# -----------------------------
def generate(schema, rows):

    data = []

    for _ in range(rows):
        row = {}

        for f in schema:
            row[f["name"]] = gen_value(f["name"], f["type"])

        data.append(row)

    return pd.DataFrame(data)

# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

# -----------------------------
# UI TABS (UNCHANGED)
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
            st.error("API Key required")
            st.stop()

        schema = extract_schema(prompt)
        schema = validate_schema(schema)

        df = generate(schema, rows)
        st.session_state.df = df

        st.success("Dataset generated")

    if st.session_state.df is not None:
        st.dataframe(st.session_state.df, height=500)

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
