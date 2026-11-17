#!/bin/bash
# Verifier for parse-malformed-csv task
# Writes 1 (pass) or 0 (fail) to /logs/verifier/reward.txt

set -euo pipefail

mkdir -p /logs/verifier

cd /app

# Step 1: Run the parser
echo "Running parse.py..." > /logs/verifier/test_output.txt
if ! python parse.py 2>&1 | tee -a /logs/verifier/test_output.txt; then
    echo "FAIL: parse.py crashed" >> /logs/verifier/test_output.txt
    echo 0 > /logs/verifier/reward.txt
    exit 0
fi

# Step 2: Check output file exists
if [ ! -f /app/data/output.json ]; then
    echo "FAIL: /app/data/output.json not created" >> /logs/verifier/test_output.txt
    echo 0 > /logs/verifier/reward.txt
    exit 0
fi

# Step 3: Validate JSON and run detailed checks
python3 << 'VERIFY_EOF' 2>&1 | tee -a /logs/verifier/test_output.txt
import json
import sys

def fail(msg):
    print(f"FAIL: {msg}")
    with open("/logs/verifier/reward.txt", "w") as f:
        f.write("0")
    sys.exit(0)

with open("/app/data/output.json") as f:
    try:
        output = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"Invalid JSON: {e}")

with open("/app/data/expected.json") as f:
    expected = json.load(f)

# Check record count
if len(output) != len(expected):
    fail(f"Expected {len(expected)} records, got {len(output)}")

# Check each record
for i, (got, exp) in enumerate(zip(output, expected)):
    for key in ["id", "name", "email", "age", "city"]:
        if key not in got:
            fail(f"Record {i}: missing key '{key}'")

        g = got[key]
        e = exp[key]

        # Type check
        if e is None:
            if g is not None:
                fail(f"Record {i}, {key}: expected null, got {g!r}")
        elif isinstance(e, int):
            if not isinstance(g, int):
                fail(f"Record {i}, {key}: expected int, got {type(g).__name__} ({g!r})")
            if g != e:
                fail(f"Record {i}, {key}: expected {e}, got {g}")
        else:
            if not isinstance(g, str):
                fail(f"Record {i}, {key}: expected str, got {type(g).__name__}")
            if g != e:
                fail(f"Record {i}, {key}: expected {e!r}, got {g!r}")

# Extra checks: no BOM/NBSP artifacts in any string field
for i, record in enumerate(output):
    for key, value in record.items():
        if isinstance(value, str):
            if '\ufeff' in value:
                fail(f"Record {i}, {key}: contains BOM character")
            if '\xa0' in value:
                fail(f"Record {i}, {key}: contains non-breaking space")
            if value != value.strip():
                fail(f"Record {i}, {key}: has leading/trailing whitespace")

# Check emails are lowercase
for i, record in enumerate(output):
    email = record.get("email")
    if email and email != email.lower():
        fail(f"Record {i}: email not lowercased: {email!r}")

# Check no extra keys
for i, record in enumerate(output):
    extra = set(record.keys()) - {"id", "name", "email", "age", "city"}
    if extra:
        fail(f"Record {i}: unexpected keys: {extra}")

print("PASS: All checks passed")
with open("/logs/verifier/reward.txt", "w") as f:
    f.write("1")
VERIFY_EOF
