import streamlit as st
import pandas as pd
import random
from openai import OpenAI
import json
import re

st.set_page_config(page_title="AI QA Data Platform", layout="wide")

# ---------- SIDEBAR ----------
st.sidebar.title("⚙️ Controls")

api_key = st.sidebar.text_input("🔐 OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

theme = st.sidebar.toggle("🌗 Dark Mode", True)
rows = st.sidebar.slider("Rows", 1, 50, 10)

# ---------- THEME ----------
if theme:
    bg = "#0f172a"; text = "white"
else:
    bg = "#ffffff"; text = "black"

st.markdown(f"""
<style>
html, body, [class*="css"] {{
background-color:{bg}; color:{text};
}}
</style>
""", unsafe_allow_html=True)

st.title("🧪 AI QA Data Platform")
st.caption("Generic • AI-driven • No hardcoding")

# ---------- REQUIREMENT INPUT ----------
requirement = st.text_area("📝 Enter Requirement",
                          placeholder="User signup with email, password, age, address")

# ---------- AI FIELD EXTRACTION ----------
def extract_fields(req):
    prompt = f"""
    Extract structured field names from this requirement:
    {req}

    Return JSON list only.
    Example: ["email", "password", "age"]
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    try:
        return json.loads(res.choices[0].message.content)
    except:
        return []

# ---------- AI DATA GENERATION ----------
def generate_data(fields, rows, req):
    prompt = f"""
    Requirement:
    {req}

    Generate {rows} rows of realistic test data.

    Fields:
    {fields}

    Return ONLY valid JSON array.
    Example:
    [
      {{"email":"a@test.com","age":25}},
      ...
    ]
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    try:
        return json.loads(res.choices[0].message.content)
    except:
        return []

# ---------- GENERATE ----------
if st.button("🚀 Generate Data"):

    if not client:
        st.error("Please enter OpenAI API key")
        st.stop()

    # Extract fields dynamically
    fields = extract_fields(requirement)

    if not fields:
        st.error("Could not detect fields from requirement")
        st.stop()

    st.success(f"Detected Fields: {fields}")

    # Generate data
    data = generate_data(fields, rows, requirement)

    if not data:
        st.error("AI data generation failed")
        st.stop()

    df = pd.DataFrame(data)

    # ---------- DISPLAY ----------
    st.subheader("📊 Generated Data")
    st.dataframe(df, use_container_width=True)

    # ---------- GENERIC VALIDATION ----------
    st.subheader("🔍 Validation Report")

    issues = {}

    for col in df.columns:
        invalid_count = 0

        for val in df[col]:
            if val is None or val == "":
                invalid_count += 1
            elif isinstance(val, str) and len(val.strip()) == 0:
                invalid_count += 1

        issues[col] = invalid_count

    for k, v in issues.items():
        st.write(f"{k} → {v} empty/invalid values")

    # ---------- MASKING (GENERIC) ----------
    if st.checkbox("🔒 Mask Data"):
        masked_df = df.copy()

        for col in masked_df.columns:
            masked_df[col] = masked_df[col].astype(str).apply(
                lambda x: x[:2] + "***" if len(x) > 2 else "***"
            )

        st.subheader("🔐 Masked Data")
        st.dataframe(masked_df)

    # ---------- EXPORT ----------
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button("📥 Download CSV", csv, "qa_data.csv")