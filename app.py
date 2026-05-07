import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import random
import json
import os
import uuid
from datetime import datetime
from openai import OpenAI

fake = Faker()

# -----------------------------
# 🔑 OPENAI CLIENT
# -----------------------------
client = OpenAI(api_key="YOUR_API_KEY")  # <-- add your key


# -----------------------------
# 🎨 UI (UNCHANGED)
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

st.title("🧠 AI Data Generator (OpenAI Powered)")


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

    def get_all(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# 🧠 OPENAI SCHEMA ENGINE
# -----------------------------
def ai_schema(prompt):

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You generate dataset schemas.

Return ONLY JSON:
{
  "domain": "...",
  "fields": [
    {"name": "...", "type": "string|int|amount|email"}
  ]
}

Rules:
- No explanation
- Minimal safe schema
- No hallucinated fields
"""
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(res.choices[0].message.content)


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


def generate(fields):
    return pd.DataFrame([
        {f["name"]: gen_value(f["type"]) for f in fields}
        for _ in range(10)
    ])


# -----------------------------
# 🧠 VERSIONING
# -----------------------------
def get_version(data, prompt):
    return f"v{len([x for x in data if x.get('prompt') == prompt]) + 1}"


def create_record(prompt, domain, fields, data_store):

    return {
        "id": str(uuid.uuid4())[:8],
        "prompt": prompt,
        "domain": domain,
        "version": get_version(data_store, prompt),
        "rows": 10,
        "cols": [f["name"] for f in fields],
        "created_at": str(datetime.now())
    }


# -----------------------------
# SESSION
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None

if "record" not in st.session_state:
    st.session_state.record = None


# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["🚀 Generate", "📂 History"])


# =============================
# 🚀 GENERATE TAB
# =============================
with tab1:

    prompt = st.text_area("💬 Describe dataset")

    if st.button("Generate with AI"):

        try:
            schema = ai_schema(prompt)

            domain = schema["domain"]
            fields = schema["fields"]

            df = generate(fields)

            st.session_state.df = df
            st.session_state.record = create_record(
                prompt, domain, fields, storage.get_all()
            )

            storage.add(st.session_state.record)

            st.success(f"{domain} dataset generated via OpenAI")

        except Exception as e:
            st.error("AI schema generation failed")
            st.exception(e)


    # -----------------------------
    # OUTPUT
    # -----------------------------
    if st.session_state.df is not None:

        st.markdown("### 📊 Generated Dataset")

        st.dataframe(st.session_state.df)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("👁 View Schema"):
                st.json(st.session_state.record)

        with col2:
            st.download_button(
                "⬇ CSV",
                st.session_state.df.to_csv(index=False),
                file_name="dataset.csv"
            )

        with col3:
            st.download_button(
                "⬇ JSON",
                json.dumps(st.session_state.record, indent=2),
                file_name="dataset.json"
            )

        if st.button("🗑 Delete Last Dataset"):

            storage.delete(st.session_state.record["id"])

            st.session_state.df = None
            st.session_state.record = None

            st.warning("Deleted last dataset")
            st.rerun()


# =============================
# 📂 HISTORY TAB
# =============================
with tab2:

    st.subheader("📂 History")

    data = storage.get_all()

    if not data:
        st.info("No history found")
        st.stop()

    search = st.text_input("🔎 Search")
    filter_domain = st.selectbox(
        "🎛️ Filter",
        ["ALL", "SAP", "MEDICAL", "BANKING", "IT", "LOGIN", "UNKNOWN"]
    )

    def match(x):

        if search and search.lower() not in x.get("prompt", "").lower():
            return False

        if filter_domain != "ALL" and x.get("domain") != filter_domain:
            return False

        return True


    filtered = [x for x in data if match(x)]

    for item in reversed(filtered):

        with st.expander(
            f"🧾 {item.get('id')} | {item.get('domain')} | {item.get('version')}"
        ):

            st.write("Prompt:", item.get("prompt"))
            st.write("Domain:", item.get("domain"))
            st.write("Version:", item.get("version"))
            st.write("Columns:", item.get("cols"))
            st.write("Time:", item.get("created_at"))

            col1, col2 = st.columns(2)

            with col1:
                if st.button("👁 Preview", key="p"+item["id"]):
                    st.json(item)

            with col2:
                if st.button("🗑 Delete", key="d"+item["id"]):
                    storage.delete(item["id"])
                    st.rerun()
