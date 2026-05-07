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

st.title("🧠 AI Data Generator")


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


storage = Storage(DATA_FILE)


# -----------------------------
# 🧠 DOMAIN DETECTION
# -----------------------------
def detect_domain(prompt):
    t = prompt.lower()

    if any(x in t for x in ["sap", "vendor", "material"]):
        return "SAP"

    if any(x in t for x in ["medical", "patient"]):
        return "MEDICAL"

    if any(x in t for x in ["bank", "account"]):
        return "BANKING"

    if any(x in t for x in ["it", "ticket"]):
        return "IT"

    if any(x in t for x in ["login", "user"]):
        return "LOGIN"

    return "UNKNOWN"


# -----------------------------
# 🧱 SCHEMA
# -----------------------------
def schema_map(domain):

    if domain == "SAP":
        return [
            ("vendor", "string"),
            ("material", "string"),
            ("quantity", "int"),
            ("price", "amount"),
            ("ship_to_party", "string"),
            ("sold_to_party", "string")
        ]

    if domain == "MEDICAL":
        return [
            ("patient", "string"),
            ("doctor", "string"),
            ("diagnosis", "string"),
            ("hospital", "string")
        ]

    if domain == "BANKING":
        return [
            ("account", "int"),
            ("balance", "amount"),
            ("transaction", "amount")
        ]

    if domain == "IT":
        return [
            ("ticket_id", "int"),
            ("issue", "string"),
            ("priority", "string")
        ]

    if domain == "LOGIN":
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

    if t == "string":
        return fake.word()

    if t == "amount":
        return round(np.random.uniform(10, 5000), 2)

    if t == "email":
        return fake.email()

    return fake.word()


def generate(schema):
    return pd.DataFrame([
        {c: gen_value(t) for c, t in schema}
        for _ in range(10)
    ])


# -----------------------------
# 🧾 RECORD
# -----------------------------
def create_record(prompt, schema, domain):
    return {
        "id": str(uuid.uuid4())[:8],
        "prompt": prompt,
        "domain": domain,
        "rows": 10,
        "cols": [c[0] for c in schema],
        "created_at": str(datetime.now())
    }


# -----------------------------
# 🧠 SESSION STATE
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "record" not in st.session_state:
    st.session_state.record = None


# -----------------------------
# 🚀 GENERATE PAGE (ONLY PAGE YOU CARE ABOUT)
# -----------------------------
prompt = st.text_area("💬 Describe dataset")

if st.button("Generate"):

    domain = detect_domain(prompt)
    schema = schema_map(domain)

    if not schema:
        st.error("⚠️ Cannot understand request safely")
        st.stop()

    df = generate(schema)
    record = create_record(prompt, schema, domain)

    st.session_state.df = df
    st.session_state.record = record

    storage.add(record)

    st.success(f"{domain} dataset generated")


# -----------------------------
# 📊 RESULT PANEL (FIRST PAGE UX)
# -----------------------------
if st.session_state.df is not None:

    st.markdown("### 📊 Generated Dataset")

    st.dataframe(st.session_state.df, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    # VIEW
    with col1:
        if st.button("👁 View Schema"):
            st.json(st.session_state.record)

    # CSV DOWNLOAD
    with col2:
        st.download_button(
            "⬇ CSV",
            st.session_state.df.to_csv(index=False),
            file_name="dataset.csv"
        )

    # JSON DOWNLOAD
    with col3:
        st.download_button(
            "⬇ JSON",
            json.dumps(st.session_state.record, indent=2),
            file_name="dataset.json"
        )

    # DELETE LAST
    if st.button("🗑 Delete Last Dataset"):

        storage.delete(st.session_state.record["id"])

        st.session_state.df = None
        st.session_state.record = None

        st.warning("Deleted last dataset")
        st.rerun()


# -----------------------------
# (OPTIONAL LIGHT HISTORY VIEW - NO UI COMPLEXITY)
# -----------------------------
with st.expander("📂 History (Simple View)"):

    try:
        data = json.load(open(DATA_FILE))
        st.write(data[-5:])
    except:
        st.write("No history")
