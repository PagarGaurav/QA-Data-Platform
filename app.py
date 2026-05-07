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
# 🎨 UI (KEEP YOUR STYLE)
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

st.title("🧠 AI Data Generator (SaaS MVP)")


# -----------------------------
# 🛡 STORAGE (SAFE)
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
                data = json.load(f)
                return data if isinstance(data, list) else []
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

    def get_all(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# 🧠 DOMAIN DETECTION
# -----------------------------
def detect_domain(prompt):
    text = prompt.lower()

    if any(x in text for x in ["sap", "purchase", "vendor", "material"]):
        return "sap"

    if any(x in text for x in ["ecommerce", "order", "product"]):
        return "ecommerce"

    if any(x in text for x in ["medical", "patient", "hospital"]):
        return "medical"

    if any(x in text for x in ["it", "ticket", "bug"]):
        return "it"

    if any(x in text for x in ["login", "user"]):
        return "login"

    return "unknown"


# -----------------------------
# 🧱 SCHEMAS
# -----------------------------
def schema_map(domain):

    if domain == "sap":
        return [
            ("vendor", "name"),
            ("material", "string"),
            ("quantity", "int"),
            ("price", "amount"),
            ("ship_to_party", "string"),
            ("sold_to_party", "string")
        ]

    if domain == "ecommerce":
        return [
            ("order_id", "int"),
            ("customer", "name"),
            ("product", "string"),
            ("price", "amount")
        ]

    if domain == "medical":
        return [
            ("patient", "name"),
            ("doctor", "name"),
            ("diagnosis", "string"),
            ("hospital", "string")
        ]

    if domain == "it":
        return [
            ("ticket_id", "int"),
            ("issue", "string"),
            ("priority", "string")
        ]

    if domain == "login":
        return [
            ("username", "string"),
            ("email", "email"),
            ("password", "string"),
            ("status", "string")
        ]

    return None


# -----------------------------
# 🧠 VALUE ENGINE
# -----------------------------
def gen_value(t):

    if t == "int":
        return random.randint(1000, 99999)

    if t == "name":
        return fake.name()

    if t == "string":
        return fake.word()

    if t == "amount":
        return round(np.random.uniform(10, 5000), 2)

    if t == "email":
        return fake.email()

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
# 🧾 RECORD
# -----------------------------
def create_record(prompt, rows, schema, domain):

    return {
        "id": str(uuid.uuid4())[:8],
        "prompt": prompt,
        "rows": rows,
        "domain": domain,
        "cols": [c[0] for c in schema] if schema else [],
        "created_at": str(datetime.now())
    }


# -----------------------------
# TABS (KEEP ORIGINAL UI)
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])


# -----------------------------
# 🚀 GENERATE
# -----------------------------
with tab1:

    prompt = st.text_area("💬 Describe dataset")

    if st.button("Generate"):

        domain = detect_domain(prompt)
        schema = schema_map(domain)

        if not schema:

            st.error("⚠️ Cannot understand request safely")
            st.stop()

        df = generate(10, schema)

        st.success(f"{domain.upper()} dataset generated")

        st.dataframe(df)

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "data.csv"
        )

        storage.add(create_record(prompt, 10, schema, domain))


# -----------------------------
# 📂 HISTORY (UPGRADED BUT SAME STYLE)
# -----------------------------
with tab2:

    st.subheader("📂 History")

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    search = st.text_input("🔎 Search")
    filter_domain = st.selectbox(
        "🎛️ Filter",
        ["ALL", "SAP", "ECOMMERCE", "MEDICAL", "IT", "LOGIN", "UNKNOWN"]
    )

    def match(x):

        if search and search.lower() not in x.get("prompt", "").lower():
            return False

        if filter_domain != "ALL" and x.get("domain", "").upper() != filter_domain:
            return False

        return True


    filtered = [x for x in data if match(x)]

    for item in reversed(filtered):

        with st.expander(f"🧾 {item.get('id')} | {item.get('domain','unknown')}"):

            st.write("Prompt:", item.get("prompt"))
            st.write("Domain:", item.get("domain"))
            st.write("Columns:", item.get("cols"))
            st.write("Rows:", item.get("rows"))
            st.write("Time:", item.get("created_at"))

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🗑 Delete", key=item["id"]):
                    storage.delete(item["id"])
                    st.rerun()

            with col2:
                st.download_button(
                    "⬇ Export",
                    json.dumps(item, indent=2),
                    file_name=f"{item['id']}.json"
                )
