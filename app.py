import streamlit as st
import pandas as pd
import random
import json
import uuid
from datetime import datetime
from faker import Faker
from openai import OpenAI

fake = Faker()

# -----------------------------
# PAGE CONFIG
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

label {
    color: white !important;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator (Enterprise Safe GPT Mode)")


# -----------------------------
# API KEY (MANDATORY FOR GPT)
# -----------------------------
api_key = st.text_input("🔑 OpenAI API Key", type="password")

client = OpenAI(api_key=api_key) if api_key else None


# -----------------------------
# STRICT TYPES
# -----------------------------
ALLOWED_TYPES = {"string", "int", "email", "phone", "amount", "id"}


# -----------------------------
# GPT → SCHEMA ONLY
# -----------------------------
def gpt_schema(prompt):

    if not client:
        return None

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You ONLY generate JSON schema.

Rules:
- No extra text
- No hallucinated fields
- Only valid types: string, int, email, phone, amount, id

Return format:
{
  "name": "Dataset",
  "fields": [
    {"name": "field", "type": "string"}
  ]
}
"""
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(res.choices[0].message.content)

    except:
        return None


# -----------------------------
# VALIDATION ENGINE (CRITICAL)
# -----------------------------
def validate_schema(schema):

    if not schema or "fields" not in schema:
        return None

    clean = []
    seen = set()

    for f in schema["fields"]:

        name = str(f.get("name", "")).strip().lower()
        t = f.get("type")

        if not name or t not in ALLOWED_TYPES:
            continue

        if name in seen:
            continue

        seen.add(name)

        clean.append({"name": name, "type": t})

    if not clean:
        return None

    return {"name": schema.get("name", "Dataset"), "fields": clean}


# -----------------------------
# DATA ENGINE (NO AI HERE)
# -----------------------------
def gen_value(f):

    name = f["name"]
    t = f["type"]

    if t == "id":
        return str(uuid.uuid4())[:10]

    if t == "string":
        if "name" in name:
            return fake.name()
        return fake.word().capitalize()

    if t == "email":
        return fake.email()

    if t == "phone":
        return "+91-" + str(random.randint(6000000000, 9999999999))

    if t == "amount":
        return round(random.uniform(1000, 50000), 2)

    if t == "int":
        return random.randint(18, 90)

    return "N/A"


# -----------------------------
# FALLBACK SCHEMA (IF GPT FAILS)
# -----------------------------
def fallback(prompt):

    text = prompt.lower()

    if "login" in text:
        return {
            "name": "Login_Data",
            "fields": [
                {"name": "username", "type": "string"},
                {"name": "password", "type": "string"},
                {"name": "email", "type": "email"},
                {"name": "device", "type": "string"}
            ]
        }

    return {
        "name": "Generic_Data",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"}
        ]
    }


# -----------------------------
# GENERATOR
# -----------------------------
def generate(schema, rows):

    schema = validate_schema(schema)

    if not schema:
        raise ValueError("Invalid schema")

    data = []

    for _ in range(rows):

        row = {}

        for f in schema["fields"]:
            row[f["name"]] = gen_value(f)

        data.append(row)

    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)

    return df


# -----------------------------
# UI INPUT
# -----------------------------
prompt = st.text_area("💬 Describe dataset")
rows = st.number_input("📊 Rows", min_value=1, value=10)


# -----------------------------
# GENERATE BUTTON
# -----------------------------
if st.button("Generate"):

    schema = gpt_schema(prompt)

    if not schema:
        schema = fallback(prompt)

    schema = validate_schema(schema)

    df = generate(schema, rows)

    st.success(f"Generated: {schema['name']}")

    st.dataframe(df)

    st.download_button("⬇ CSV", df.to_csv(index=False), "data.csv")

    st.download_button("⬇ JSON", json.dumps(schema, indent=2), "schema.json")
