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
# SAFE EMAIL
# -----------------------------
def safe_email():
    return f"{fake.user_name()}@gmail.com"

# -----------------------------
# NAME CLEAN FIX (MAIN ISSUE RESOLVED)
# -----------------------------
def clean_name():
    full = fake.name()
    parts = full.split()

    # ensure only first + last (max 2 words)
    if len(parts) >= 2:
        return parts[0] + " " + parts[1]
    return full

# -----------------------------
# VALUE ENGINE (FIXED NAME ISSUE)
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

    # ✅ FIXED NAME HANDLING (MAIN FIX)
    if "name" in n:
        return clean_name()

    if "diagnosis" in n:
        return random.choice(["Diabetes","Asthma","Flu","Infection"])

    if "age" in n:
        return random.randint(1, 90)

    if t == "int":
        return random.randint(1, 9999)

    if t == "float":
        return round(random.uniform(100, 100000), 2)

    if t == "date":
        return fake.date_this_year().isoformat()

    return None

# -----------------------------
# GENERATOR
# -----------------------------
def generate(schema, rows):

    data = []

    for _ in range(rows):
        row = {}

        for f in schema:
            val = gen_value(f["name"], f["type"])
            if val is not None:
                row[f["name"]] = val

        data.append(row)

    return pd.DataFrame(data)

# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])

with tab1:

    prompt = st.text_area("💬 Describe dataset")
    rows = st.number_input("📊 Rows", min_value=1, value=10)

    if st.button("Generate"):

        if not client:
            st.error("API Key required")
            st.stop()

        # minimal schema fallback (keep your existing logic if already present)
        schema = [{"name": "id", "type": "id"},
                  {"name": "name", "type": "name"}]

        df = generate(schema, rows)
        st.session_state.df = df

        st.success("Dataset generated")

    if st.session_state.df is not None:
        st.dataframe(st.session_state.df, height=500)
