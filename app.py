def smart_infer_fields(prompt):

    text = prompt.lower()

    # Try to extract intent but DO NOT hardcode domains
    fields = []

    # Always include ID if anything looks like dataset request
    fields.append({"name": "id", "type": "id"})

    # GENERIC DETECTION (NOT DOMAIN FIXED)

    if any(k in text for k in ["user", "login", "account", "auth"]):
        fields += [
            {"name": "username", "type": "name"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "status", "type": "string"}
        ]

    elif any(k in text for k in ["customer", "bank", "loan", "account"]):
        fields += [
            {"name": "name", "type": "name"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "address", "type": "address"},
            {"name": "amount", "type": "amount"},
            {"name": "status", "type": "string"}
        ]

    elif any(k in text for k in ["medical", "patient", "hospital"]):
        fields += [
            {"name": "patient_name", "type": "name"},
            {"name": "age", "type": "int"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "diagnosis", "type": "string"},
            {"name": "status", "type": "string"}
        ]

    elif any(k in text for k in ["sap", "vendor", "po", "purchase"]):
        fields += [
            {"name": "vendor_name", "type": "name"},
            {"name": "vendor_id", "type": "id"},
            {"name": "material", "type": "id"},
            {"name": "quantity", "type": "int"},
            {"name": "amount", "type": "amount"},
            {"name": "status", "type": "string"}
        ]

    elif any(k in text for k in ["it", "ticket", "bug", "issue"]):
        fields += [
            {"name": "ticket_id", "type": "id"},
            {"name": "user", "type": "name"},
            {"name": "issue", "type": "string"},
            {"name": "priority", "type": "string"},
            {"name": "status", "type": "string"}
        ]

    else:
        # GENERIC SAFE MODE (IMPORTANT)
        fields += [
            {"name": "name", "type": "name"},
            {"name": "email", "type": "email"},
            {"name": "phone", "type": "phone"},
            {"name": "status", "type": "string"}
        ]

    return fields
