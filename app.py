import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime

fake = Faker()

# -----------------------------
# 🎨 UI
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
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Generator (NO-GUESS SAFE MODE)")


# -----------------------------
# 🛡 STORAGE
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

    def get(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# 🧠 INTENT DETECTION
# -----------------------------
def detect_intent(prompt):
    text = prompt.lower()

    if any(x in text for x in ["login", "signup", "authentication"]):
        return "functional"

    return "domain"


def detect_domain(prompt):
    text = prompt.lower()

    if any(x in text for x in ["sap", "purchase order", "vendor", "plant"]):
        return "sap"

    if any(x in text for x in ["ecommerce", "order", "product", "cart"]):
        return "ecommerce"

    if any(x in text for x in ["medical", "patient", "hospital"]):
        return "medical"

    if any(x in text for x in ["it", "ticket", "bug", "issue"]):
        return "it"

    return "unknown"


# -----------------------------
# 🧱 SCHEMAS
# -----------------------------
def sap_schema():
    return [
        ("po_number", "int"),
        ("vendor_name", "name"),
        ("vendor_email", "email"),
        ("material_code", "int"),
        ("plant", "string"),
        ("quantity", "int"),
        ("unit_price", "amount"),
        ("status", "string"),
        ("po_date", "datetime")
    ]


def ecommerce_schema():
    return [
        ("order_id", "int"),
        ("customer_name", "name"),
        ("email", "email"),
        ("product", "string"),
        ("price", "amount"),
        ("status", "string")
    ]


def medical_schema():
    return [
        ("patient_id", "int"),
        ("patient_name", "name"),
        ("age", "int"),
        ("doctor", "name"),
        ("diagnosis", "string"),
        ("hospital", "string")
    ]


def it_schema():
    return [
        ("ticket_id", "int"),
        ("user_name", "name"),
        ("issue", "string"),
        ("priority", "string"),
        ("status", "string")
    ]


def login_schema():
    return [
        ("user_id", "int"),
        ("username", "string"),
        ("email", "email"),
        ("password", "string"),
        ("login_status", "string"),
        ("device", "string")
    ]


def get_schema(domain, intent):
    if intent == "functional":
        return login_schema()

    if domain == "sap":
        return sap_schema()

    if domain == "ecommerce":
        return ecommerce_schema()

    if domain == "medical":
        return medical_schema()

    if domain == "it":
        return it_schema()

    return None


# -----------------------------
# 🧠 VALUE ENGINE
# -----------------------------
def gen_value(t):

    if t == "int":
        return random.randint(1000, 99999)

    if t == "name":
        return fake.name()

    if t == "email":
        return fake.user_name() + "@gmail.com"

    if t == "string":
        return fake.word()

    if t == "amount":
        return round(np.random.uniform(10, 5000), 2)

    if t == "datetime":
        return fake.date_between(start_date="-2y", end_date="today")

    return fake.word()


def generate(rows, schema):
    data = []

    for i in range(rows):
        row = {}

        for col, typ in schema:
            if col.endswith("id"):
                row[col] = i + 1
            else:
                row[col] = gen_value(typ)

        data.append(row)

    return pd.DataFrame(data)


# -----------------------------
# 🚀 PARSE + NO-GUESS RULE
# -----------------------------
def parse(prompt):

    intent = detect_intent(prompt)
    domain = detect_domain(prompt)

    schema = get_schema(domain, intent)

    return intent, domain, schema


# -----------------------------
# UI
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])


# -----------------------------
# 🚀 GENERATE
# -----------------------------
with tab1:

    prompt = st.text_area("💬 Describe dataset")

    if st.button("Generate"):

        intent, domain, schema = parse(prompt)

        # ❌ SAFE MODE: ASK QUESTIONS
        if schema is None or domain == "unknown":

            st.error("⚠️ I cannot generate this safely without clarity.")

            st.markdown("### ❓ Please specify:")

            st.write("""
- System type: SAP / Ecommerce / Medical / IT / Login test  
- Entity: users / orders / patients / tickets  
- Fields needed (if custom)
- Purpose (testing / performance / validation)
""")

            st.stop()

        rows = 10
        if "10k" in prompt.lower():
            rows = 10000

        df = generate(rows, schema)

        st.success(f"Generated {domain.upper()} / {intent.upper()} dataset")

        st.dataframe(df.head(20))

        st.metric("Rows", len(df))
        st.metric("Columns", len(df.columns))

        st.download_button("Download CSV", df.to_csv(index=False), "data.csv")

        storage.add({
            "id": str(uuid.uuid4())[:8],
            "prompt": prompt,
            "domain": domain,
            "intent": intent,
            "rows": rows
        })


# -----------------------------
# 📂 HISTORY
# -----------------------------
with tab2:

    st.subheader("📂 Generated History")

    for item in reversed(storage.get()):

        st.markdown(f"""
### 🧾 {item['id']}
- Prompt: {item['prompt']}
- Domain: {item['domain']}
- Intent: {item['intent']}
- Rows: {item['rows']}
""")