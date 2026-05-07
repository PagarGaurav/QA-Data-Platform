import streamlit as st
import pandas as pd
import random
import json
import os
import uuid
from datetime import datetime
from faker import Faker

fake = Faker()

# -----------------------------
# YOUR ORIGINAL UI (UNCHANGED)
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

st.title("🧠 AI Data Generator")


# -----------------------------
# STORAGE (PRESERVED LOGIC)
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

    def get_all(self):
        return self._read()


storage = Storage(DATA_FILE)


# -----------------------------
# 🔐 ENTERPRISE DATA ENGINE (ONLY FIXED PART)
# -----------------------------

ALLOWED_TYPES = {"string", "int", "email", "phone", "amount", "id"}


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

        clean.append({
            "name": name,
            "type": t
        })

    if not clean:
        return None

    return {
        "name": schema.get("name", "Dataset"),
        "fields": clean
    }


def generate_value(field):

    name = field["name"]
    t = field["type"]

    if t == "id":
        return str(uuid.uuid4())[:10]

    if t == "string":

        if "name" in name:
            return fake.name()

        if "city" in name:
            return fake.city()

        if "country" in name:
            return fake.country()

        if "product" in name:
            return fake.word().capitalize()

        return fake.word().capitalize()

    if t == "email":
        return fake.email()

    if t == "phone":
        return "+91-" + str(random.randint(6000000000, 9999999999))

    if t == "amount":
        return round(random.uniform(500, 100000), 2)

    if t == "int":
        return random.randint(18, 90)

    return "N/A"


def generate_data(schema, rows):

    schema = validate_schema(schema)

    if not schema:
        raise ValueError("Invalid schema")

    data = []

    for _ in range(rows):
        row = {}
        for f in schema["fields"]:
            row[f["name"]] = generate_value(f)
        data.append(row)

    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)

    return df


# -----------------------------
# SESSION STATE (UNCHANGED UI BEHAVIOR)
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = None


# -----------------------------
# UI INPUT (UNCHANGED)
# -----------------------------
prompt = st.text_area("💬 Describe dataset")
rows = st.number_input("📊 Rows", min_value=1, value=10)


# -----------------------------
# GENERATE (ONLY ENGINE REPLACED)
# -----------------------------
if st.button("Generate"):

    # ⚠️ You can replace this with your GPT schema later if needed
    schema = {
        "name": "Dataset",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"}
        ]
    }

    df = generate_data(schema, rows)

    st.session_state.df = df

    # SAVE HISTORY (UNCHANGED STRUCTURE)
    storage.add({
        "id": str(uuid.uuid4())[:8],
        "prompt": prompt,
        "rows": rows,
        "created_at": str(datetime.now()),
        "fields": schema["fields"]
    })

    st.success("Dataset generated safely")


# -----------------------------
# MAIN OUTPUT (UNCHANGED UI STYLE)
# -----------------------------
if st.session_state.df is not None:
    st.dataframe(st.session_state.df)

    st.download_button(
        "⬇ CSV",
        st.session_state.df.to_csv(index=False),
        "data.csv"
    )

    st.download_button(
        "⬇ JSON",
        st.session_state.df.to_json(orient="records"),
        "data.json"
    )


# -----------------------------
# 📂 HISTORY TAB (UNCHANGED UI STRUCTURE)
# -----------------------------
st.markdown("## 📂 Generator History")

for item in reversed(storage.get_all()):

    st.markdown(f"""
### 🧾 {item.get('id')}
- Prompt: {item.get('prompt')}
- Rows: {item.get('rows')}
- Time: {item.get('created_at')}
""")
