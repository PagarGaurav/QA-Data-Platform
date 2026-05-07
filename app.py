import streamlit as st
import pandas as pd
import random
import json
import os
import uuid
from faker import Faker
from datetime import datetime

fake = Faker()

# -----------------------------
# 🎨 SAAS UI
# -----------------------------
st.set_page_config(page_title="AI Data Copilot SaaS", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #0b0f19;
    color: #e5e7eb;
}

.block-container {
    padding-top: 2rem;
}

.stButton > button {
    background: linear-gradient(90deg, #6366f1, #3b82f6);
    color: white;
    border-radius: 10px;
    border: none;
}

.stTextInput > div > div > input {
    background-color: #111827;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Copilot SaaS (MVP)")


# -----------------------------
# 🗂 STORAGE (MULTI USER READY)
# -----------------------------
DATA_FILE = "copilot_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_FILE)


# -----------------------------
# 🧠 SESSION STATE (COPILOT MEMORY)
# -----------------------------
if "schema" not in st.session_state:
    st.session_state.schema = []

if "domain" not in st.session_state:
    st.session_state.domain = None

if "step" not in st.session_state:
    st.session_state.step = 0

if "chat" not in st.session_state:
    st.session_state.chat = []


# -----------------------------
# 🧠 DOMAIN DETECTION
# -----------------------------
def detect_domain(text):

    text = text.lower()

    if any(x in text for x in ["sap", "vendor", "material", "purchase", "po"]):
        return "sap"

    if any(x in text for x in ["health", "patient", "doctor", "hospital"]):
        return "health"

    if any(x in text for x in ["bank", "account", "loan", "transaction"]):
        return "banking"

    return "generic"


# -----------------------------
# 🧠 COPILOT QUESTIONS
# -----------------------------
def next_question(domain, schema):

    if domain == "sap":
        flow = [
            "Which SAP object? (PO / Sales Order / Vendor Master)",
            "Do you need pricing fields? (yes/no)",
            "Do you need Ship-to & Sold-to parties? (yes/no)"
        ]

    elif domain == "health":
        flow = [
            "Which entity? (Patient / Doctor / Appointment)",
            "Need diagnosis fields? (yes/no)",
            "Need hospital details? (yes/no)"
        ]

    elif domain == "banking":
        flow = [
            "Which object? (Account / Loan / Transaction)",
            "Need balance & interest? (yes/no)",
            "Need branch info? (yes/no)"
        ]

    else:
        flow = [
            "What dataset do you want?",
            "List fields separated by comma"
        ]

    if len(schema) < len(flow):
        return flow[len(schema)]

    return None


# -----------------------------
# 🧠 SCHEMA BUILDER
# -----------------------------
def update_schema(input_text):

    text = input_text.lower()

    if "yes" in text:
        st.session_state.schema.append(("extra_field", "string"))

    elif "," in input_text:
        fields = [x.strip() for x in input_text.split(",")]
        for f in fields:
            st.session_state.schema.append((f, "string"))


# -----------------------------
# 🧠 DATA GENERATION
# -----------------------------
def gen_value():
    return fake.word()

def generate(schema):
    data = []

    for i in range(10):
        row = {}

        for col, _ in schema:
            row[col] = gen_value()

        data.append(row)

    return pd.DataFrame(data)


# -----------------------------
# 🧠 UI LAYOUT
# -----------------------------
col1, col2 = st.columns([2, 1])

# LEFT: COPILOT CHAT
with col1:

    st.subheader("💬 Copilot Chat")

    user_input = st.text_input("Talk to Copilot")

    if st.button("Send"):

        # INIT DOMAIN
        if st.session_state.domain is None:
            st.session_state.domain = detect_domain(user_input)

        # UPDATE SCHEMA
        update_schema(user_input)

        st.session_state.chat.append(("user", user_input))

        # CHECK NEXT STEP
        q = next_question(st.session_state.domain, st.session_state.schema)

        if q:
            st.session_state.chat.append(("ai", q))
        else:

            st.success("Schema complete. Generating dataset...")

            df = generate(st.session_state.schema)

            st.dataframe(df)

            st.download_button(
                "Download CSV",
                df.to_csv(index=False),
                "dataset.csv"
            )

            # SAVE TO SaaS HISTORY
            data = load_data()

            uid = str(uuid.uuid4())[:8]

            data[uid] = {
                "schema": st.session_state.schema,
                "domain": st.session_state.domain,
                "created_at": str(datetime.now())
            }

            save_data(data)

            # RESET COPILOT
            st.session_state.schema = []
            st.session_state.domain = None
            st.session_state.chat = []


    # CHAT DISPLAY
    for role, msg in st.session_state.chat:
        if role == "user":
            st.markdown(f"🧑‍💻 **You:** {msg}")
        else:
            st.markdown(f"🤖 **Copilot:** {msg}")


# RIGHT: SaaS PANEL
with col2:

    st.subheader("📦 SaaS Dashboard")

    data = load_data()

    if not data:
        st.info("No datasets yet")
    else:
        for k, v in data.items():

            st.markdown(f"""
### 🧾 Dataset {k}
- Domain: {v.get('domain','')}
- Created: {v.get('created_at','')}
- Fields: {v.get('schema',[])}
""")

            if st.button(f"Delete {k}"):
                del data[k]
                save_data(data)
                st.rerun()
