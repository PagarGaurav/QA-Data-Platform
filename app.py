import uuid
import random
from faker import Faker

fake = Faker()

# -----------------------------
# STRICT TYPE SYSTEM
# -----------------------------
ALLOWED_TYPES = {"string", "int", "email", "phone", "amount", "id"}


# -----------------------------
# CLEAN VALUE GENERATOR (NO BAD DATA)
# -----------------------------
def generate_value(field):

    name = field["name"].lower()
    t = field["type"]

    # ID (always stable format)
    if t == "id" or "id" in name:
        return str(uuid.uuid4())[:10]

    # STRING (context-aware, not random junk)
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

    # EMAIL (always valid format)
    if t == "email":
        return fake.email()

    # PHONE (strict valid format)
    if t == "phone":
        return "+91-" + str(random.randint(6000000000, 9999999999))

    # AMOUNT (realistic financial range)
    if t == "amount":
        return round(random.uniform(500, 100000), 2)

    # INT (bounded realistic values)
    if t == "int":
        return random.randint(18, 90)

    return "N/A"


# -----------------------------
# SCHEMA VALIDATION (NO INVALID COLUMNS)
# -----------------------------
def validate_schema(schema):

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


# -----------------------------
# DATA GENERATION (NO SCHEMA DRIFT)
# -----------------------------
def generate_data(schema, rows):

    schema = validate_schema(schema)

    if not schema:
        raise ValueError("Invalid schema after validation")

    dataset = []

    for _ in range(rows):

        row = {}

        for field in schema["fields"]:
            value = generate_value(field)

            # final safety check
            if value is None:
                value = "N/A"

            row[field["name"]] = value

        dataset.append(row)

    return dataset
