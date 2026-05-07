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
# 🎨 UI (MODERN DARK SAAS)
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
    border: none;
    padding: 0.5rem 1rem;
}

[data-testid="stMetric"] {
    background-color: #111827;
    padding: 10px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Data Generator (Enterprise Safe)")


# -----------------------------
# 🛡 SAFE STORAGE
# -----------------------------
DATA_FILE = "storage.json"


class SafeStorage:
    def __init__(self, file):
        self.file = file
        self.ensure()

    def ensure(self):
        if not os.path.exists(self.file):
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
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, self.file)

    def get_all(self):
        return self._read()

    def add(self, item):
        data = self._read()
        data.append(item)
        self._write(data)

    def delete(self, item_id):
        data = self._read()
        data = [x for x in data if x.get("id") != item_id]
        self._write(data)


storage = SafeStorage(DATA_FILE)


# -----------------------------
# 🧠 DOMAIN DETECTION
# -----------------------------
def detect_domain(prompt):
    text = prompt.lower()

    if any(x in text for x in ["sap", "purchase order", "po", "vendor", "plant"]):
        return "sap"

    if any(x in text for x in ["ecommerce", "order", "product", "cart", "payment"]):
        return "ecommerce"

    if any(x in text for x in ["medical", "patient", "hospital", "doctor"]):
        return "medical"

    if any(x in text for x in ["it", "ticket", "incident", "bug", "issue"]):
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
        ("currency", "currency"),
        ("status", "string"),
        ("po_date", "datetime")
    ]


def ecommerce_schema():
    return [
        ("order_id", "int"),
        ("customer_name", "name"),
        ("customer_email", "email"),
        ("product", "string"),
        ("category", "string"),
        ("quantity", "int"),
        ("price", "amount"),
        ("payment_method", "string"),
        ("status", "string"),
        ("order_date", "datetime")
    ]


def medical_schema():
    return [
        ("patient_id", "int"),
        ("patient_name", "name"),
        ("age", "age"),
        ("gender", "string"),
        ("doctor", "name"),
        ("diagnosis", "string"),
        ("medicine", "string"),
        ("hospital", "string"),
        ("visit_date", "datetime")
    ]


def it_schema():
    return [
        ("ticket_id", "int"),
        ("user_name", "name"),
        ("email", "email"),
        ("issue_type", "string"),
        ("priority", "string"),
        ("status", "string"),
        ("assigned_to", "name"),
        ("created_date", "datetime")
    ]


def get_schema(domain):
    if domain == "sap":
        return sap_schema()
    if domain == "ecommerce":
        return ecommerce_schema()
    if domain == "medical":
        return medical_schema()
    if domain == "it":
        return it_schema()
    return []


# -----------------------------
# 🧠 VALUE ENGINE
# -----------------------------
def generate_email():
    return fake.user_name() + "@" + random.choice(["gmail.com", "yahoo.com", "outlook.com"])


def gen_value(t):
    if t == "int":
        return random.randint(1000, 999999)
    if t == "name":
        return fake.name()
    if t == "email":
        return generate_email()
    if t == "string":
        return fake.word()
    if t == "amount":
        return round(np.random.uniform(50, 5000), 2)
    if t == "datetime":
        return fake.date_between(start_date="-3y", end_date="today")
    if t == "age":
        return random.randint(18, 80)
    if t == "currency":
        return random.choice(["INR", "USD", "EUR"])
    return fake.word()


def generate_table(rows, cols):
    data = []

    for i in range(rows):
        row = {}

        for name, t in cols:
            if name.endswith("id") or name == "po_number" or name == "order_id" or name == "ticket_id":
                row[name] = i + 1
            else:
                row[name] = gen_value(t)

        data.append(row)

    return pd.DataFrame(data)


# -----------------------------
# 🧾 RECORD
# -----------------------------
def create_record(prompt, rows, cols, domain):
    return {
        "id": str(uuid.uuid4())[:8],
        "prompt": prompt,
        "rows": rows,
        "cols": [c[0] for c in cols],
        "domain": domain,
        "created_at": str(datetime.now())
    }


# -----------------------------
# 🎯 PARSE + INTELLIGENCE
# -----------------------------
def parse_request(prompt):

    domain = detect_domain(prompt)

    # ❌ UNKNOWN DOMAIN HANDLING
    if domain == "unknown":
        return None, None, None

    rows = 10
    text = prompt.lower()

    if "10k" in text:
        rows = 10000

    cols = get_schema(domain)

    return rows, cols, domain


# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "🎬 Gallery"])


# -----------------------------
# 🚀 GENERATE
# -----------------------------
with tab1:

    prompt = st.text_area("💬 Describe dataset")

    if st.button("Generate"):

        rows, cols, domain = parse_request(prompt)

        # ❌ UNKNOWN HANDLING (IMPORTANT)
        if domain is None:
            st.error("⚠️ I could not understand your request clearly.")

            st.markdown("### ❓ Please specify one of these:")
            st.write("""
- SAP Purchase Order dataset  
- Ecommerce order dataset  
- Medical patient dataset  
- IT ticket dataset  
""")
            st.stop()

        df = generate_table(rows, cols)

        st.success(f"Generated {domain.upper()} dataset")

        st.session_state["last_df"] = df

        record = create_record(prompt, rows, cols, domain)
        storage.add(record)

        # PREVIEW
        st.subheader("📊 Preview")
        st.dataframe(df.head(15))

        # METRICS
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", len(df))
        c2.metric("Columns", len(df.columns))
        c3.metric("Nulls", int(df.isnull().sum().sum()))

        # DOWNLOAD
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "dataset.csv"
        )


# -----------------------------
# 🎬 GALLERY (NETFLIX STYLE)
# -----------------------------
with tab2:

    st.subheader("🎬 Dataset Gallery")

    history = storage.get_all()

    if not history:
        st.info("No datasets yet")
    else:

        for item in reversed(history):

            st.markdown(f"""
### 📦 {item.get('domain','UNKNOWN').upper()}
- Prompt: {item.get('prompt')}
- Rows: {item.get('rows')}
- Columns: {item.get('cols')}
- Time: {item.get('created_at')}
""")

            if st.button(f"🗑 Delete {item['id']}", key=item["id"]):
                storage.delete(item["id"])
                st.rerun()
