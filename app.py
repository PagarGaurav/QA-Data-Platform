import random
import uuid
from faker import Faker

fake = Faker()

# -----------------------------
# ONLY FIX: DATA ENGINE LAYER
# -----------------------------

ALLOWED_TYPES = {"string", "int", "email", "phone", "amount", "id"}


def validate_schema(schema):
    """DO NOT CHANGE UI - ONLY CLEAN DATA SCHEMA"""

    if not schema or "fields" not in schema:
        return None

    clean_fields = []
    seen = set()

    for f in schema["fields"]:

        name = str(f.get("name", "")).strip().lower()
        t = f.get("type")

        # reject invalid schema fields
        if not name or t not in ALLOWED_TYPES:
            continue

        # prevent duplicate columns
        if name in seen:
            continue

        seen.add(name)

        clean_fields.append({
            "name": name,
            "type": t
        })

    if not clean_fields:
        return None

    return {
        "name": schema.get("name", "Dataset"),
        "fields": clean_fields
    }


def generate_value(field):

    name = field["name"].lower()
    t = field["type"]

    # ID
    if t == "id":
        return str(uuid.uuid4())[:10]

    # STRING (context-aware only)
    if t == "string":

        if "name" in name:
            return fake.name()

        if "city" in name:
            return fake.city()

        if "country" in name:
            return fake.country()

        return fake.word().capitalize()

    # EMAIL
    if t == "email":
        return fake.email()

    # PHONE (valid format only)
    if t == "phone":
        return "+91-" + str(random.randint(6000000000, 9999999999))

    # AMOUNT (realistic)
    if t == "amount":
        return round(random.uniform(1000, 100000), 2)

    # INT (bounded)
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

    return data
